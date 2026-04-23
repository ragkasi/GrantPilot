"""PDF parsing and text chunking pipeline.

parse_pdf()   — extracts per-page text from a PDF file using PyMuPDF.
chunk_pages() — splits page text into RAG-ready chunks with citation metadata.

Chunk design goals:
- Each chunk is ≤ CHUNK_MAX_CHARS characters (fits a typical LLM context window slot).
- Chunks never cross page boundaries so page_number citations are exact.
- chunk_index is monotonically increasing across the whole document.
- document_name is stored on every chunk for citation generation without joins.
"""
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

CHUNK_MAX_CHARS = 1_200
CHUNK_MIN_CHARS = 60  # discard chunks shorter than this (headers, footers, stray whitespace)


@dataclass
class ParsedPage:
    page_number: int  # 1-indexed
    text: str


@dataclass
class ChunkData:
    document_id: str
    document_name: str
    page_number: int
    chunk_index: int   # monotonically increasing across the whole document
    chunk_text: str


def parse_pdf(file_path: Path) -> list[ParsedPage]:
    """Extract text from each page of a PDF. Returns pages with non-empty text."""
    pages: list[ParsedPage] = []
    try:
        doc = fitz.open(str(file_path))
    except Exception as exc:
        raise ValueError(f"Could not open PDF: {exc}") from exc

    for i in range(len(doc)):
        text = doc[i].get_text().strip()
        if text:
            pages.append(ParsedPage(page_number=i + 1, text=text))

    doc.close()
    return pages


def chunk_pages(
    pages: list[ParsedPage],
    document_id: str,
    document_name: str,
) -> list[ChunkData]:
    """Convert parsed pages into chunks with citation metadata.

    Each page's text is split at paragraph boundaries (double newlines).
    Paragraphs are accumulated until the chunk would exceed CHUNK_MAX_CHARS,
    at which point the current accumulation is flushed as a chunk.
    Chunks shorter than CHUNK_MIN_CHARS are discarded (stray headers/footers).
    """
    chunks: list[ChunkData] = []
    global_index = 0

    for page in pages:
        page_chunks = _split_page(page.text, page.page_number, document_id, document_name, global_index)
        chunks.extend(page_chunks)
        global_index += len(page_chunks)

    return chunks


def _split_page(
    text: str,
    page_number: int,
    document_id: str,
    document_name: str,
    start_index: int,
) -> list[ChunkData]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    result: list[ChunkData] = []
    current_parts: list[str] = []
    current_len = 0

    def flush(parts: list[str], idx: int) -> int:
        combined = " ".join(parts).strip()
        if len(combined) >= CHUNK_MIN_CHARS:
            result.append(
                ChunkData(
                    document_id=document_id,
                    document_name=document_name,
                    page_number=page_number,
                    chunk_index=idx,
                    chunk_text=combined,
                )
            )
            return idx + 1
        return idx

    chunk_idx = start_index
    for para in paragraphs:
        # Compute the length of the joined result if we include this paragraph.
        potential_len = len(" ".join(current_parts + [para]))
        if potential_len > CHUNK_MAX_CHARS and current_parts:
            chunk_idx = flush(current_parts, chunk_idx)
            current_parts = [para]
            current_len = len(para)
        else:
            current_parts.append(para)
            current_len = potential_len

    if current_parts:
        chunk_idx = flush(current_parts, chunk_idx)

    return result
