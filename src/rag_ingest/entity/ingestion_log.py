from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..orm import Base

if TYPE_CHECKING:
    from .ingestion_queue_item import IngestionQueueItem

class IngestionLog(Base):
    __tablename__ = "ingestion_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    ingestion_queue_item_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_queue_item.id"), nullable=False
    )
    level: Mapped[str] = mapped_column(String(50), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ingestion_queue_item: Mapped[IngestionQueueItem] = relationship(
        "IngestionQueueItem", back_populates="logs"
    )
