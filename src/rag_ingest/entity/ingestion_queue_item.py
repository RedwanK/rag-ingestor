from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..orm import Base
from .queue_status import QueueStatus

if TYPE_CHECKING:
    from .document_node import DocumentNode
    from .ingestion_log import IngestionLog


class IngestionQueueItem(Base):
    __tablename__ = "ingestion_queue_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_node_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_node.id"), nullable=True
    )
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[QueueStatus] = mapped_column(
        Enum(QueueStatus), default=QueueStatus.queued, nullable=False
    )
    rag_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[DocumentNode | None] = relationship(
        "DocumentNode", back_populates="ingestion_queue_items"
    )
    logs: Mapped[list["IngestionLog"]] = relationship(
        "IngestionLog", back_populates="ingestion_queue_item", cascade="all, delete-orphan"
    )
