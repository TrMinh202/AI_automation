"""
Ingest BCM/spec documents (PDF or plain text) into the Qdrant bcm_specs collection.

Usage:
    python scripts/ingest_bcm.py path/to/bcm_document.pdf
    python scripts/ingest_bcm.py path/to/spec.txt
    python scripts/ingest_bcm.py data/BCM_VF34.pdf data/other_spec.pdf  # multiple files
"""
import logging
import sys
from itertools import islice

from qdrant_client.http.models import PointStruct

from app.clients.gemini_client import GeminiClient
from app.clients.qdrant_client import QdrantClientWrapper
from app.config import settings
from app.ingestion.pdf_loader import chunk_point_id, load_document

logger = logging.getLogger(__name__)

_BATCH_SIZE = 16


def _chunks(iterable, size: int):
    it = iter(iterable)
    while batch := list(islice(it, size)):
        yield batch


def ingest_bcm(file_paths: list[str]) -> int:
    gemini_client = GeminiClient()
    bcm_client    = QdrantClientWrapper(settings.bcm_collection_name)
    bcm_client.ensure_collection()

    total = 0
    for file_path in file_paths:
        logger.info("Loading document: %s", file_path)
        doc_chunks = load_document(file_path)
        logger.info("  → %d chunks to ingest", len(doc_chunks))

        for batch in _chunks(doc_chunks, _BATCH_SIZE):
            texts    = [c.text for c in batch]
            vectors  = gemini_client.embed_batch(texts)

            points = [
                PointStruct(
                    id=chunk_point_id(c.source_file, c.page, c.chunk_index),
                    vector=vector,
                    payload={
                        "text":        c.text,
                        "source_file": c.source_file,
                        "page":        c.page,
                        "chunk_index": c.chunk_index,
                    },
                )
                for c, vector in zip(batch, vectors)
            ]
            bcm_client.upsert(points)
            total += len(points)
            logger.info("  Upserted batch of %d chunks (total so far: %d)", len(points), total)

    logger.info("Done. Ingested %d chunks into collection '%s'", total, settings.bcm_collection_name)
    return total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_bcm.py <doc1.pdf> [doc2.pdf ...]")
        sys.exit(1)
    count = ingest_bcm(sys.argv[1:])
    print(f"Ingested {count} chunks total.")
