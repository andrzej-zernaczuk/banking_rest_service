from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from banking_rest_service.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for use in FastAPI dependencies."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
