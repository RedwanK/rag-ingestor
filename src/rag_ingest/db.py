from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_database_url

Base = declarative_base()


def get_engine(url: str | None = None):
    return create_engine(url or get_database_url(), pool_pre_ping=True, future=True)


def get_session_maker(url: str | None = None):
    engine = get_engine(url)
    return sessionmaker(bind=engine, autoflush=False, future=True)


def create_schema(url: str | None = None) -> None:
    engine = get_engine(url)
    Base.metadata.create_all(engine)
