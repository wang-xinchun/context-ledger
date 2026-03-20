"""DB bootstrap helpers for local development and tests."""

from __future__ import annotations

from app.db.base import Base
import app.db.models as _models  # noqa: F401  # Ensure model metadata is registered.
from app.db.session import get_engine


def init_db() -> None:
    """Create all tables from ORM metadata (mainly for local bootstrap/tests)."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
