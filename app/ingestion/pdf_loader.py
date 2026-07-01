"""
Load and chunk BCM/spec documents (PDF or plain text) for RAG ingestion.

Chunking strategy:
- Target chunk size: ~1000 characters
- Overlap: ~200 characters (to avoid cutting mid-sentence context)
- Each chunk carries metadata: source_file, page, chunk_index
"""
import hashlib
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_CHUNK_SIZE    = 1000
_CHUNK_OVERLAP = 200


@dataclass
class DocChunk:
    text: str
    source_file: str
    page: int          # 0-based; 0 for plain-text files
    chunk_index: int   # position within the page


def _split_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Split a long string into overlapping chunks, breaking at whitespace boundaries."""
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Try to end at a sentence/word boundary
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunks.append(text[start:end].strip())
        # Always advance forward; overlap must not exceed progress
        next_start = end - overlap
        if next_start <= start:
            next_start = end  # no overlap possible, just move forward
        start = next_start
    return [c for c in chunks if c]


def load_pdf(file_path: str) -> list[DocChunk]:
    """Extract text from a PDF and split into chunks."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required: pip install pypdf") from exc

    path = Path(file_path)
    reader = PdfReader(str(path))
    chunks: list[DocChunk] = []

    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if not text:
            continue
        for chunk_idx, chunk_text in enumerate(_split_text(text)):
            chunks.append(DocChunk(
                text=chunk_text,
                source_file=path.name,
                page=page_idx,
                chunk_index=chunk_idx,
            ))
        logger.debug("Page %d → %d chunks", page_idx, chunk_idx + 1 if text else 0)

    logger.info("Loaded %d chunks from %s (%d pages)", len(chunks), path.name, len(reader.pages))
    return chunks


def load_text(file_path: str) -> list[DocChunk]:
    """Load a plain-text document and split into chunks."""
    path = Path(file_path)
    text = path.read_text(encoding="utf-8", errors="replace")
    chunks = [
        DocChunk(text=c, source_file=path.name, page=0, chunk_index=i)
        for i, c in enumerate(_split_text(text))
    ]
    logger.info("Loaded %d chunks from %s", len(chunks), path.name)
    return chunks


def load_document(file_path: str) -> list[DocChunk]:
    """Auto-detect format and load document into chunks."""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return load_pdf(file_path)
    if suffix in (".txt", ".md"):
        return load_text(file_path)
    raise ValueError(f"Unsupported document type: {suffix}. Supported: .pdf, .txt, .md")


def chunk_point_id(source_file: str, page: int, chunk_index: int) -> str:
    digest = hashlib.sha256(f"{source_file}:{page}:{chunk_index}".encode()).hexdigest()
    return str(uuid.UUID(hex=digest[:32]))
