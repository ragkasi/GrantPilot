"""Local file storage abstraction.

All callers must go through the public functions below — never access
_upload_root() directly. To swap to S3 or Supabase Storage, replace the
four public functions; no other code needs to change.

Public interface (swap points):
  save_file()   — persist an uploaded document; returns storage_url
  save_report() — persist a generated PDF report; returns storage_url
  get_file_path() — resolve storage_url → absolute Path (local only)
  file_exists() — check whether a storage_url resolves to an existing file

storage_url format: "{project_id}/{filename}" — relative to upload_dir,
so it stays portable across machines and container restarts.
"""
from pathlib import Path

from app.core.config import settings


def _upload_root() -> Path:
    return Path(settings.upload_dir)


def save_file(content: bytes, project_id: str, doc_id: str, filename: str) -> str:
    """Persist an uploaded document and return its storage_url."""
    dest_dir = _upload_root() / project_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Prefix with doc_id to avoid collisions from same-named uploads.
    safe_name = f"{doc_id}_{filename}"
    (_upload_root() / project_id / safe_name).write_bytes(content)
    return f"{project_id}/{safe_name}"


def save_report(pdf_bytes: bytes, project_id: str) -> str:
    """Persist a generated PDF report and return its storage_url."""
    dest_dir = _upload_root() / project_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "report.pdf").write_bytes(pdf_bytes)
    return f"{project_id}/report.pdf"


def get_file_path(storage_url: str) -> Path:
    """Resolve a storage_url to an absolute Path on disk."""
    return _upload_root() / storage_url


def file_exists(storage_url: str) -> bool:
    """Return True if the storage_url resolves to an existing file."""
    return get_file_path(storage_url).exists()
