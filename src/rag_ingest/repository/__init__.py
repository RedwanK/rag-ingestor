"""Aggregate repository exports for DB access."""

from .ingestion_log_repo import IngestionLogRepo
from .ingestion_queue_item_repo import IngestionQueueItemRepo

__all__ = [
    IngestionLogRepo,
    IngestionQueueItemRepo
]
