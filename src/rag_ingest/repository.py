from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import asc, select, update
from sqlalchemy.orm import Session

from .entity import IngestionLog, IngestionQueueItem, QueueStatus


def get_next_queued(session: Session) -> Optional[IngestionQueueItem]:
    statement = (
        select(IngestionQueueItem)
        .where(IngestionQueueItem.status == QueueStatus.queued)
        .order_by(asc(IngestionQueueItem.created_at))
        .limit(1)
    )
    return session.execute(statement).scalar_one_or_none()


def has_processing(session: Session) -> bool:
    statement = select(IngestionQueueItem).where(
        IngestionQueueItem.status == QueueStatus.processing
    )
    return session.execute(statement).first() is not None


def reserve_for_processing(
    session: Session, item: IngestionQueueItem, started_at: Optional[datetime] = None
) -> IngestionQueueItem:
    started_at = started_at or datetime.now(timezone.utc)
    item.status = QueueStatus.processing
    item.started_at = started_at
    session.add(item)
    session.flush()
    return item


def mark_indexed(
    session: Session, item: IngestionQueueItem, rag_message: str | None = None
) -> IngestionQueueItem:
    item.status = QueueStatus.indexed
    item.ended_at = datetime.now(timezone.utc)
    item.rag_message = rag_message
    session.add(item)
    session.flush()
    return item


def mark_failed(
    session: Session,
    item: IngestionQueueItem,
    status: QueueStatus = QueueStatus.failed,
    rag_message: str | None = None,
) -> IngestionQueueItem:
    item.status = status
    item.ended_at = datetime.now(timezone.utc)
    item.rag_message = rag_message
    session.add(item)
    session.flush()
    return item


def log_event(
    session: Session,
    ingestion_queue_item_id: int,
    message: str,
    level: str = "info",
) -> IngestionLog:
    log = IngestionLog(ingestion_queue_item_id=ingestion_queue_item_id, message=message, level=level, created_at=datetime.now(), updated_at=datetime.now())
    session.add(log)
    session.flush()
    return log


def reset_stale_processing(session: Session, timeout_seconds: float) -> list[int]:
    """Reset processing items older than the timeout back to queued and return their ids."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)

    stale_ids = (
        session.execute(
            select(IngestionQueueItem.id).where(
                IngestionQueueItem.status == QueueStatus.processing,
                IngestionQueueItem.started_at.is_not(None),
                IngestionQueueItem.started_at < cutoff,
            )
        )
        .scalars()
        .all()
    )
    if not stale_ids:
        return []

    session.execute(
        update(IngestionQueueItem)
        .where(IngestionQueueItem.id.in_(stale_ids))
        .values(
            status=QueueStatus.queued,
            started_at=None,
            ended_at=None,
            rag_message="reset to queued after timeout",
        )
    )
    for queue_item_id in stale_ids:
        log_event(
            session,
            queue_item_id=queue_item_id,
            level="warning",
            message="job reset to queued after exceeding processing timeout",
        )
    return stale_ids
