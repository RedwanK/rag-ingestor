from __future__ import annotations

"""Database engine/session utilities shared across repositories."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import Config

Base = declarative_base()

def get_engine(url: str | None = None):
    """Create a SQLAlchemy engine using the provided URL or the default config."""
    return create_engine(url or Config.get_database_url(), pool_pre_ping=True, future=True)


def get_session_maker(url: str | None = None):
    """Return a configured sessionmaker bound to a fresh engine."""
    engine = get_engine(url)
    return sessionmaker(bind=engine, autoflush=False, future=True)


def create_schema(url: str | None = None) -> None:
    """Create all mapped tables in the target database if they do not exist."""
    engine = get_engine(url)
    Base.metadata.create_all(engine)
