"""SQLAlchemy engine, session factory, and FastAPI dependency."""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine — defaults to local SQLite for dev; override DATABASE_URL for Postgres
# ---------------------------------------------------------------------------
_DB_URL = settings.database_url or "sqlite:///./grantpilot.db"

engine = create_engine(
    _DB_URL,
    # SQLite needs check_same_thread=False for multi-threaded use in dev
    connect_args={"check_same_thread": False} if _DB_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_all_tables() -> None:
    """Creates all tables from the current metadata. Used on startup and in tests."""
    from app.models import base  # noqa: F401 — registers all models via imports below
    from app.models import analysis, chunk, document, organization, project  # noqa: F401

    base.Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context-manager session — used in non-request code (lifespan, seed)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
