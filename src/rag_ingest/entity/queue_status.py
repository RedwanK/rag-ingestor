from __future__ import annotations

"""Enumerated states for items moving through the ingestion queue."""

import enum

class QueueStatus(str, enum.Enum):
    """Discrete states covering the ingestion lifecycle."""
    queued = "queued"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"
    download_failed = "download_failed"
