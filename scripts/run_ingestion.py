import logging
import sys

from app.ingestion.ingest import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_ingestion.py <excel_file_path> [column_mapping.yaml]")
        sys.exit(1)
    file_path = sys.argv[1]
    mapping_path = sys.argv[2] if len(sys.argv) > 2 else "config/column_mapping.yaml"
    count = main(file_path, mapping_path)
    print(f"Ingested {count} rows from {file_path}")
