from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class QueueStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    DOWNLOAD_FAILED = "download_failed"


class DocumentNode(Base):
    __tablename__ = "document_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    queue_items: Mapped[list["IngestionQueueItem"]] = relationship(
        "IngestionQueueItem", back_populates="document", cascade="all, delete-orphan"
    )


class IngestionQueueItem(Base):
    __tablename__ = "ingestion_queue_items"
    __table_args__ = (
        Index("ix_ingestion_queue_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_node_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_nodes.id"), nullable=True
    )
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[QueueStatus] = mapped_column(
        Enum(QueueStatus), default=QueueStatus.QUEUED, nullable=False
    )
    rag_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[DocumentNode | None] = relationship(
        "DocumentNode", back_populates="queue_items"
    )
    logs: Mapped[list["IngestionLog"]] = relationship(
        "IngestionLog", back_populates="queue_item", cascade="all, delete-orphan"
    )


class IngestionLog(Base):
    __tablename__ = "ingestion_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    queue_item_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_queue_items.id"), nullable=False
    )
    level: Mapped[str] = mapped_column(String(50), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    queue_item: Mapped[IngestionQueueItem] = relationship(
        "IngestionQueueItem", back_populates="logs"
    )
