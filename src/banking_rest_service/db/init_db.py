from __future__ import annotations

# Import models so they are registered with Base.metadata
import banking_rest_service.models  # noqa: F401
from banking_rest_service.db.base import Base
from banking_rest_service.db.session import engine


def init_db() -> None:
    """Create all database tables in the configured SQLite database."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
