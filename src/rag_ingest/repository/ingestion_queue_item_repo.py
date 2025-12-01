from __future__ import annotations

"""Repository for querying and mutating ingestion queue items."""

from typing import Optional

from datetime import datetime, timedelta, timezone
from sqlalchemy import asc, select, update
from sqlalchemy.orm import Session

from ..entity import IngestionQueueItem, QueueStatus

class IngestionQueueItemRepo:
    session: Session = None

    def __init__(self, session):
        """Store the active DB session used for subsequent operations."""
        self.session = session

    def find_next_queued_item(self) -> Optional[IngestionQueueItem]:
        """Fetch the oldest job still marked as queued."""
        statement = (
            select(IngestionQueueItem)
            .where(IngestionQueueItem.status == QueueStatus.queued)
            .order_by(asc(IngestionQueueItem.created_at))
            .limit(1)
        )
        return self.session.execute(statement).scalar_one_or_none()
    
    def find_one_by_id(self, id): 
        """Return a queue item by primary key or None."""
        return self.session.get(IngestionQueueItem, id)
    
    def has_processing_item(self) -> bool:
        """Check whether any job is currently marked as processing."""
        statement = select(IngestionQueueItem).where(
            IngestionQueueItem.status == QueueStatus.processing
        )
        return self.session.execute(statement).first() is not None

    def reserve_item_for_processing(
        self,
        item: IngestionQueueItem, 
        started_at: Optional[datetime] = None
    ) -> IngestionQueueItem:
        """Mark a queued item as processing and set its start time."""
        item.status = QueueStatus.processing
        item.started_at = started_at or datetime.now(timezone.utc)
        self.session.add(item)
        self.session.flush()
        return item

    def mark_indexed(
        self,
        item: IngestionQueueItem, 
        rag_message: str | None = None
    ) -> IngestionQueueItem:
        """Flag an item as successfully indexed and record a completion timestamp."""
        item.status = QueueStatus.indexed
        item.ended_at = datetime.now(timezone.utc)
        item.rag_message = rag_message
        self.session.add(item)
        self.session.flush()
        return item
    
    def mark_failed(
        self,
        item: IngestionQueueItem,
        rag_message: str | None = None,
    ) -> IngestionQueueItem:
        """Move an item to failed with an optional error message."""
        item.status = QueueStatus.failed
        item.ended_at = datetime.now(timezone.utc)
        item.rag_message = rag_message
        self.session.add(item)
        self.session.flush()
        return item
    
    def reset_stale_processing_items(
        self,
        timeout_seconds: float
    ) -> list[int]:
        """Reset processing items older than the timeout back to queued and return their ids."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)

        stale_ids = (
            self.session.execute(
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

        self.session.execute(
            update(IngestionQueueItem)
            .where(IngestionQueueItem.id.in_(stale_ids))
            .values(
                status=QueueStatus.queued,
                started_at=None,
                ended_at=None,
                rag_message="resetted to queued after timeout",
            )
        )

        return stale_ids
