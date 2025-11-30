from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rag_ingest.db import Base
from rag_ingest.models import IngestionQueueItem, QueueStatus
from rag_ingest.worker import run_worker


class StubRagAnything:
    def __init__(self):
        self.processed: list[Path] = []

    async def process_document_complete(self, file_path: Path):
        self.processed.append(Path(file_path))


class StubRagProvider:
    def __init__(self):
        self.rag_anything = StubRagAnything()


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'worker.sqlite'}", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, future=True)


@pytest.mark.asyncio
async def test_worker_processes_queue_and_marks_indexed(tmp_path, session_factory):
    shared_root = tmp_path / "shared"
    shared_root.mkdir()
    source_file = shared_root / "doc.txt"
    source_file.write_text("content")

    with session_factory() as session:
        item = IngestionQueueItem(storage_path="doc.txt")
        session.add(item)
        session.commit()

    async def provider_factory(_):
        return StubRagProvider()

    await run_worker(
        session_factory=session_factory,
        shared_root=shared_root,
        rag_storage_dir=tmp_path / "rag",
        poll_interval=0.1,
        exit_on_idle=True,
        rag_provider_factory=provider_factory,
    )

    with session_factory() as session:
        refreshed = session.get(IngestionQueueItem, item.id)
        assert refreshed.status == QueueStatus.indexed
        assert refreshed.ended_at is not None
        assert "successfully" in (refreshed.rag_message or "").lower()


@pytest.mark.asyncio
async def test_missing_file_marks_download_failed(tmp_path, session_factory):
    shared_root = tmp_path / "shared"
    shared_root.mkdir()

    with session_factory() as session:
        item = IngestionQueueItem(storage_path="missing.txt")
        session.add(item)
        session.commit()

    async def provider_factory(_):
        return StubRagProvider()

    await run_worker(
        session_factory=session_factory,
        shared_root=shared_root,
        rag_storage_dir=tmp_path / "rag",
        poll_interval=0.1,
        exit_on_idle=True,
        rag_provider_factory=provider_factory,
    )

    with session_factory() as session:
        refreshed = session.get(IngestionQueueItem, item.id)
        assert refreshed.status == QueueStatus.download_failed
        assert "file not found" in (refreshed.rag_message or "").lower()
