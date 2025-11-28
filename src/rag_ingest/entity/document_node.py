from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..orm import Base

if TYPE_CHECKING:
    from .ingestion_queue_item import IngestionQueueItem

class DocumentNode(Base):
    __tablename__ = "document_node"

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

    ingestion_queue_items: Mapped[list["IngestionQueueItem"]] = relationship(
        "IngestionQueueItem", back_populates="document", cascade="all, delete-orphan"
    )
