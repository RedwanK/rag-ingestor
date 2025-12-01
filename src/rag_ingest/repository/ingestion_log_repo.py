from __future__ import annotations

"""Repository wrapper to persist ingestion log entries."""

from datetime import datetime
from sqlalchemy.orm import Session

from ..entity import IngestionLog

class IngestionLogRepo:
    session: Session = None

    def __init__(self, session):
        """Store the active DB session used to write logs."""
        self.session = session

    def add_ingestion_log(
        self,
        ingestion_queue_item_id: int,
        message: str,
        level: str = "info",
    ) -> IngestionLog:
        """Create and persist a new ingestion log row."""
        log = IngestionLog(
            ingestion_queue_item_id=ingestion_queue_item_id, 
            message=message, 
            level=level, 
            created_at=datetime.now(), 
            updated_at=datetime.now()
        )

        self.session.add(log)
        self.session.flush()

        return log
