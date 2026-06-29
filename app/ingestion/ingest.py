import logging

from app.clients.gemini_client import GeminiClient
from app.clients.qdrant_client import QdrantClientWrapper
from app.ingestion.build_payload import build_embedding_text, build_point, parse_list_cell
from app.ingestion.column_mapping import load_column_mapping
from app.ingestion.excel_loader import load_excel

logger = logging.getLogger(__name__)


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main(file_path: str, mapping_path: str = "config/column_mapping.yaml", batch_size: int = 32) -> int:
    mapping = load_column_mapping(mapping_path)
    df = load_excel(file_path, mapping)

    gemini_client = GeminiClient()
    qdrant_client = QdrantClientWrapper()
    qdrant_client.ensure_collection()

    rows = df.to_dict("records")
    total_ingested = 0

    for batch in _chunks(rows, batch_size):
        prepared_rows = []
        for row in batch:
            preconditions = parse_list_cell(row.get("preconditions"), mapping.list_delimiter)
            steps_action = parse_list_cell(row.get("steps_action"), mapping.list_delimiter)
            steps_expected = parse_list_cell(row.get("steps_expected"), mapping.list_delimiter)
            steps = [
                {"action": a, "expected_result": e}
                for a, e in zip(steps_action, steps_expected)
            ]
            prepared_rows.append(
                {
                    **row,
                    "preconditions": preconditions,
                    "steps": steps,
                }
            )

        texts = [build_embedding_text(row) for row in prepared_rows]
        vectors = gemini_client.embed_batch(texts)

        points = [
            build_point(
                row=row,
                row_index=int(row["_source_row_index"]),
                source_file=file_path,
                sheet_name=str(mapping.sheet_name or "default"),
                embedding=vector,
            )
            for row, vector in zip(prepared_rows, vectors)
        ]
        qdrant_client.upsert(points)
        total_ingested += len(points)

    logger.info("Ingested %s rows from %s", total_ingested, file_path)
    return total_ingested


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python -m app.ingestion.ingest <excel_file_path> [column_mapping.yaml]")
        sys.exit(1)
    path = sys.argv[1]
    mapping_arg = sys.argv[2] if len(sys.argv) > 2 else "config/column_mapping.yaml"
    count = main(path, mapping_arg)
    print(f"Ingested {count} rows from {path}")
