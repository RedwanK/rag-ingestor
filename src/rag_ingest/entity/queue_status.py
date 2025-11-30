from __future__ import annotations

import enum

class QueueStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"
    download_failed = "download_failed"
