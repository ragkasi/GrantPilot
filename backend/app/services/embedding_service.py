"""Embedding generation and cosine-similarity retrieval.

Default backend: TF-IDF hash vectors (256-dim, pure Python, no API key).
OpenAI backend: text-embedding-3-small (1536-dim) when OPENAI_API_KEY is set.

The `embed_text` / `find_similar_chunks` interface is stable so the entire
embedding backend can be swapped in Phase 5 (e.g. pgvector + native index)
without touching callers.
"""
import logging
import math
from collections import Counter

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chunk import DocumentChunk
from app.models.document import Document

logger = logging.getLogger(__name__)

_TFIDF_DIM = 256  # dimensionality of the hash-based fallback


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def embed_text(text: str) -> list[float]:
    """Return an embedding vector for the given text."""
    if settings.openai_api_key:
        try:
            return _openai_embed(text)
        except Exception as exc:
            logger.warning("OpenAI embedding failed, falling back to TF-IDF: %s", exc)
    return _tfidf_embed(text)


def embed_chunks_for_project(db: Session, project_id: str) -> int:
    """Populate embedding_json for every unembedded chunk in a project.

    Returns the number of chunks that were embedded.
    Chunks that fail silently are skipped so partial progress is preserved.
    """
    chunks = (
        db.query(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(
            Document.project_id == project_id,
            DocumentChunk.embedding_json.is_(None),
        )
        .all()
    )

    count = 0
    for chunk in chunks:
        try:
            chunk.embedding_json = embed_text(chunk.chunk_text)
            count += 1
        except Exception as exc:
            logger.warning("Skipping embedding for chunk %s: %s", chunk.id, exc)

    if count:
        db.flush()

    logger.info("Embedded %d chunks for project %s", count, project_id)
    return count


def find_similar_chunks(
    db: Session,
    query_text: str,
    project_id: str,
    exclude_document_types: list[str] | None = None,
    top_k: int = 5,
) -> list[DocumentChunk]:
    """Return the top_k most relevant chunks for query_text within a project.

    Chunks from excluded document types are skipped (e.g. the grant opportunity
    document itself should not be cited as nonprofit evidence).
    Falls back to keyword overlap when a chunk has no embedding.
    """
    query_vec = embed_text(query_text)

    q = (
        db.query(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(Document.project_id == project_id)
    )
    if exclude_document_types:
        q = q.filter(Document.document_type.notin_(exclude_document_types))

    chunks = q.all()
    if not chunks:
        return []

    scored: list[tuple[float, DocumentChunk]] = []
    for chunk in chunks:
        if chunk.embedding_json:
            score = _cosine(query_vec, chunk.embedding_json)
        else:
            score = _keyword_overlap(query_text, chunk.chunk_text)
        scored.append((score, chunk))

    scored.sort(key=lambda t: -t[0])
    return [c for _, c in scored[:top_k]]


# ---------------------------------------------------------------------------
# Similarity helpers
# ---------------------------------------------------------------------------

def cosine_similarity(a: list[float], b: list[float]) -> float:
    return _cosine(a, b)


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (norm_a * norm_b)


def _keyword_overlap(query: str, text: str) -> float:
    """Jaccard-like overlap over lowercased tokens — used when no embedding."""
    q_tokens = set(query.lower().split())
    t_tokens = set(text.lower().split())
    if not q_tokens:
        return 0.0
    return len(q_tokens & t_tokens) / len(q_tokens)


# ---------------------------------------------------------------------------
# Embedding backends
# ---------------------------------------------------------------------------

def _tfidf_embed(text: str) -> list[float]:
    """256-dimensional bag-of-words hash embedding, L2-normalised."""
    tokens = text.lower().split()
    counts = Counter(tokens)
    vec = [0.0] * _TFIDF_DIM
    for word, count in counts.items():
        # Deterministic placement via hash
        idx = abs(hash(word)) % _TFIDF_DIM
        vec[idx] += float(count)
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _openai_embed(text: str) -> list[float]:
    import openai  # optional dependency
    client = openai.OpenAI(api_key=settings.openai_api_key)
    resp = client.embeddings.create(model="text-embedding-3-small", input=text[:8000])
    return resp.data[0].embedding
