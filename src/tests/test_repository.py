from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rag_ingest.db import Base
from rag_ingest.models import IngestionLog, IngestionQueueItem, QueueStatus
from rag_ingest.repository import (
    get_next_queued,
    log_event,
    mark_indexed,
    reset_stale_processing,
    reserve_for_processing,
)


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'test.sqlite'}", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, future=True)


def test_queue_selection_orders_by_created_at(session_factory):
    with session_factory() as session:
        older = IngestionQueueItem(
            storage_path="old.pdf",
            status=QueueStatus.QUEUED,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        newer = IngestionQueueItem(
            storage_path="new.pdf",
            status=QueueStatus.QUEUED,
        )
        session.add_all([newer, older])
        session.commit()

    with session_factory() as session:
        next_item = get_next_queued(session)
        assert next_item.storage_path == "old.pdf"


def test_marking_and_logging(session_factory):
    with session_factory() as session:
        item = IngestionQueueItem(storage_path="file.pdf")
        session.add(item)
        session.commit()
        reserve_for_processing(session, item)
        session.commit()

    with session_factory() as session:
        item = session.get(IngestionQueueItem, item.id)
        assert item.status == QueueStatus.PROCESSING
        mark_indexed(session, item, rag_message="ok")
        log_event(session, queue_item_id=item.id, message="finished")
        session.commit()

    with session_factory() as session:
        item = session.get(IngestionQueueItem, item.id)
        assert item.status == QueueStatus.INDEXED
        assert item.rag_message == "ok"
        logs = session.query(IngestionLog).filter_by(queue_item_id=item.id).all()
        assert len(logs) == 1
        assert "finished" in logs[0].message


def test_reset_stale_jobs(session_factory):
    stale_started = datetime.now(timezone.utc) - timedelta(hours=2)
    with session_factory() as session:
        stale = IngestionQueueItem(
            storage_path="stale.pdf",
            status=QueueStatus.PROCESSING,
            started_at=stale_started,
        )
        session.add(stale)
        session.commit()

    with session_factory() as session:
        reset_ids = reset_stale_processing(session, timeout_seconds=1800)
        session.commit()

    assert stale.id in reset_ids

    with session_factory() as session:
        updated = session.get(IngestionQueueItem, stale.id)
        assert updated.status == QueueStatus.QUEUED
        assert updated.started_at is None
        assert updated.rag_message == "reset to queued after timeout"
        logs = session.query(IngestionLog).filter_by(queue_item_id=stale.id).all()
        assert len(logs) == 1
        assert "reset to queued" in logs[0].message
