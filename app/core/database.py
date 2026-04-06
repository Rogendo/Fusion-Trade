"""SQLite database engine and session management via SQLModel."""
from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

# Ensure the data directory exists
Path(settings.DATABASE_URL.replace('sqlite:///', '')).parent.mkdir(
    parents=True, exist_ok=True
)

# connect_args required for SQLite to enable WAL mode and thread safety
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={'check_same_thread': False},
)


def init_db() -> None:
    """Create all tables. Called on app startup."""
    # Import all models so SQLModel registers them before create_all
    from app.models import (
        user, journal, model_registry, 
        email_verification, password_reset,
        news_cache
    )
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a database session."""
    with Session(engine) as session:
        yield session
