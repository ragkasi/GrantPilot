"""Local file storage abstraction.

Stores uploaded files under upload_dir/{project_id}/{doc_id}_{filename}.
The storage_url saved to the DB is the path relative to upload_dir, so it
can be rehydrated with get_file_path() without baking in absolute paths.

Swap this module for an S3/Supabase implementation in production by replacing
save_file() and get_file_path() — the rest of the codebase stays the same.
"""
from pathlib import Path

from app.core.config import settings


def _upload_root() -> Path:
    return Path(settings.upload_dir)


def save_file(content: bytes, project_id: str, doc_id: str, filename: str) -> str:
    """Persist bytes to disk and return the storage_url (relative path)."""
    dest_dir = _upload_root() / project_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Prefix filename with doc_id to avoid collisions from same-named uploads.
    safe_name = f"{doc_id}_{filename}"
    dest = dest_dir / safe_name
    dest.write_bytes(content)

    # Return path relative to upload_dir so DB records are not host-absolute.
    return f"{project_id}/{safe_name}"


def get_file_path(storage_url: str) -> Path:
    """Resolve a storage_url back to an absolute Path on disk."""
    return _upload_root() / storage_url
