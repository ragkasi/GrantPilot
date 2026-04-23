"""Unit tests for document_parser — no DB or HTTP required."""
import fitz
import pytest

from app.services.document_parser import (
    CHUNK_MAX_CHARS,
    CHUNK_MIN_CHARS,
    ChunkData,
    ParsedPage,
    chunk_pages,
    parse_pdf,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf_file(tmp_path, pages: list[str], name: str = "test.pdf") -> object:
    """Creates a multi-page PDF on disk and returns its path."""
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((50, 72), text)
    path = tmp_path / name
    doc.save(str(path))
    doc.close()
    return path


def _make_pdf_bytes(pages: list[str]) -> bytes:
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((50, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


# ---------------------------------------------------------------------------
# parse_pdf tests
# ---------------------------------------------------------------------------

def test_parse_pdf_single_page(tmp_path) -> None:
    path = _make_pdf_file(tmp_path, ["Hello, World!"])
    pages = parse_pdf(path)
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Hello" in pages[0].text


def test_parse_pdf_multiple_pages(tmp_path) -> None:
    path = _make_pdf_file(tmp_path, ["Page one content.", "Page two content.", "Page three."])
    pages = parse_pdf(path)
    assert len(pages) == 3
    assert pages[0].page_number == 1
    assert pages[1].page_number == 2
    assert pages[2].page_number == 3


def test_parse_pdf_skips_blank_pages(tmp_path) -> None:
    """Pages with no extractable text are skipped."""
    doc = fitz.open()
    doc.new_page()  # blank page
    p = doc.new_page()
    p.insert_text((50, 72), "Non-blank page")
    path = tmp_path / "sparse.pdf"
    doc.save(str(path))
    doc.close()

    pages = parse_pdf(path)
    assert len(pages) == 1
    assert pages[0].page_number == 2


def test_parse_pdf_invalid_file_raises(tmp_path) -> None:
    bad = tmp_path / "corrupt.pdf"
    bad.write_bytes(b"not a pdf")
    with pytest.raises(ValueError, match="Could not open PDF"):
        parse_pdf(bad)


def test_parse_pdf_empty_raises(tmp_path) -> None:
    empty = tmp_path / "empty.pdf"
    empty.write_bytes(b"")
    with pytest.raises(ValueError):
        parse_pdf(empty)


# ---------------------------------------------------------------------------
# chunk_pages tests
# ---------------------------------------------------------------------------

def test_chunk_pages_basic(tmp_path) -> None:
    text = "This is a paragraph about STEM programs that is long enough to meet the minimum threshold."
    pages = [ParsedPage(page_number=1, text=text)]
    chunks = chunk_pages(pages, document_id="doc_1", document_name="test.pdf")
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.document_id == "doc_1"
    assert chunk.document_name == "test.pdf"
    assert chunk.page_number == 1
    assert chunk.chunk_index == 0
    assert "STEM" in chunk.chunk_text


def test_chunk_pages_index_is_monotonic_across_pages(tmp_path) -> None:
    pages = [
        ParsedPage(page_number=1, text="First page content with some text."),
        ParsedPage(page_number=2, text="Second page content with more text."),
        ParsedPage(page_number=3, text="Third page content."),
    ]
    chunks = chunk_pages(pages, document_id="doc_1", document_name="report.pdf")
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks))), "chunk_index must be monotonically increasing"


def test_chunk_pages_page_number_preserved(tmp_path) -> None:
    pages = [
        ParsedPage(page_number=1, text="Page one contains a description of the STEM mentoring program and its outcomes."),
        ParsedPage(page_number=3, text="Page three contains budget information for the fiscal year ending December 2024."),
    ]
    chunks = chunk_pages(pages, document_id="doc_1", document_name="report.pdf")
    page_numbers = {c.page_number for c in chunks}
    assert 1 in page_numbers
    assert 3 in page_numbers


def test_chunk_pages_long_text_splits(tmp_path) -> None:
    # Create a page with text longer than CHUNK_MAX_CHARS split into paragraphs
    paragraph = "A" * 400
    long_text = "\n\n".join([paragraph] * 5)  # 5 × 400 = 2000 chars, > CHUNK_MAX_CHARS
    pages = [ParsedPage(page_number=1, text=long_text)]
    chunks = chunk_pages(pages, document_id="doc_1", document_name="long.pdf")
    assert len(chunks) > 1, "Long page text should produce multiple chunks"
    for chunk in chunks:
        assert len(chunk.chunk_text) <= CHUNK_MAX_CHARS


def test_chunk_pages_short_text_discarded() -> None:
    # Text shorter than CHUNK_MIN_CHARS should produce no chunk
    pages = [ParsedPage(page_number=1, text="Hi")]
    chunks = chunk_pages(pages, document_id="doc_1", document_name="tiny.pdf")
    assert len(chunks) == 0


def test_chunk_pages_empty_pages_list() -> None:
    chunks = chunk_pages([], document_id="doc_1", document_name="empty.pdf")
    assert chunks == []


def test_chunk_pages_denormalized_metadata() -> None:
    pages = [ParsedPage(page_number=2, text="Mission: serve communities across Ohio with evidence-based programs.")]
    chunks = chunk_pages(pages, document_id="doc_abc", document_name="mission.pdf")
    assert len(chunks) == 1
    c = chunks[0]
    # Citation metadata must be self-contained on every chunk
    assert c.document_id == "doc_abc"
    assert c.document_name == "mission.pdf"
    assert c.page_number == 2


def test_parse_and_chunk_roundtrip(tmp_path) -> None:
    """End-to-end: parse a real PDF from disk, then chunk it."""
    content = "BrightPath serves 312 students annually through STEM mentoring.\n\n" * 3
    page2 = "Annual operating budget is $420,000 with program expenses broken out by quarter for fiscal year 2024."
    path = _make_pdf_file(tmp_path, [content, page2])
    pages = parse_pdf(path)
    chunks = chunk_pages(pages, document_id="doc_e2e", document_name="annual_report.pdf")

    assert len(chunks) >= 1
    doc_ids = {c.document_id for c in chunks}
    assert doc_ids == {"doc_e2e"}
    page_numbers = {c.page_number for c in chunks}
    assert 1 in page_numbers
    assert 2 in page_numbers
