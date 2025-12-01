from __future__ import annotations

"""Background worker that polls the ingestion queue and processes items sequentially."""

import asyncio
import logging
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Optional

from sqlalchemy.orm import sessionmaker

from .orm import (
    Config,
    get_session_maker
)
from .entity import IngestionQueueItem, QueueStatus
from .repository import IngestionQueueItemRepo, IngestionLogRepo
from .services import RAGProvider

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def resolve_storage_path(shared_root: Path, relative_path: str) -> Path:
    """Convert a queue item's relative storage path into an absolute file path."""
    return (shared_root / relative_path).resolve()


async def process_queue_item(
    ingestion_log_repo: IngestionLogRepo,
    ingestion_queue_item_repo: IngestionQueueItemRepo,
    queue_item: IngestionQueueItem,
    shared_root: Path,
    rag_provider: RAGProvider,
) -> None:
    """Handle a single queue item lifecycle: load file, ingest it, and record results."""
    queue_item = ingestion_queue_item_repo.find_one_by_id(queue_item.id)

    abs_path = resolve_storage_path(shared_root, queue_item.storage_path)
    if not abs_path.exists() or not abs_path.is_file():
        logger.error("File missing or unreadable: %s", abs_path)

        ingestion_queue_item_repo.mark_failed(
            queue_item,
            rag_message=f"File not found at {abs_path}",
        )

        ingestion_log_repo.add_ingestion_log(
            ingestion_queue_item_id=queue_item.id,
            level="error",
            message=f"Unable to open file at {abs_path}",
        )

        return

    try:
        await rag_provider.rag_anything.process_document_complete(file_path=abs_path)

        ingestion_queue_item_repo.mark_indexed(
            queue_item,
            rag_message="Ingestion completed successfully",
        )

        ingestion_log_repo.add_ingestion_log(
            ingestion_queue_item_id=queue_item.id,
            level="info",
            message=f"Successfully ingested {queue_item.storage_path}",
        )
        
    except Exception as exc:
        logger.exception("Ingestion failed for queue item %s", queue_item.id)

        ingestion_queue_item_repo.mark_failed(
            queue_item,
            status=QueueStatus.failed,
            rag_message=str(exc),
        )

        ingestion_log_repo.add_ingestion_log(
            ingestion_queue_item_id=queue_item.id,
            level="error",
            message=f"Failed to ingest {queue_item.storage_path}: {exc}",
        )


async def run_worker(
    *,
    session_factory: Optional[sessionmaker] = None,
    shared_root: Optional[Path] = None,
    rag_storage_dir: Optional[Path] = None,
    poll_interval: Optional[float] = None,
    processing_timeout: Optional[float] = None,
    exit_on_idle: bool = False,
    rag_provider_factory: Optional[Callable[[Path], Awaitable[RAGProvider]]] = None,
) -> None:
    """Main worker loop that polls for jobs, reserves one at a time, and ingests it."""
    session_factory = session_factory or get_session_maker()
    shared_root = shared_root or Config.get_shared_storage_dir()
    rag_storage_dir = rag_storage_dir or Config.get_rag_storage_dir()
    poll_interval = poll_interval or Config.get_poll_interval_seconds()
    processing_timeout = processing_timeout or Config.get_processing_timeout_seconds()
    rag_provider_factory = rag_provider_factory or (lambda path: RAGProvider(path))

    shared_root.mkdir(parents=True, exist_ok=True)
    rag_provider = await rag_provider_factory(rag_storage_dir)

    stop_event = asyncio.Event()

    def _handle_stop(signame: str):
        """Signal handler to request a graceful shutdown."""
        logger.info("Received %s, stopping worker loop", signame)
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_stop, sig.name)
        except NotImplementedError:
            # Signals may not be available on some platforms (e.g., Windows)
            pass

    while not stop_event.is_set():
        with session_factory() as session:
            session.expire_on_commit=False
            ingestion_queue_item_repo = IngestionQueueItemRepo(session)
            ingestion_log_repo = IngestionLogRepo(session)

            reset_ids = ingestion_queue_item_repo.reset_stale_processing_items(processing_timeout)

            if reset_ids:
                for queue_item_id in reset_ids:
                    ingestion_log_repo.add_ingestion_log(
                        ingestion_queue_item_id=queue_item_id,
                        level="warning",
                        message="job resetted to queued after exceeding processing timeout",
                    )
                session.commit()
                logger.warning("Reset %s stale jobs to queued", reset_ids)

            if ingestion_queue_item_repo.has_processing_item():
                logger.info("Another worker is already processing a job; exiting")
                return

            queue_item = ingestion_queue_item_repo.find_next_queued_item()
            if queue_item is None:
                session.commit()
                if exit_on_idle:
                    return
                await asyncio.sleep(poll_interval)
                continue

            ingestion_queue_item_repo.reserve_item_for_processing(queue_item, started_at=datetime.now(timezone.utc))
            ingestion_log_repo.add_ingestion_log(
                ingestion_queue_item_id=queue_item.id,
                level="info",
                message="Job reserved for processing",
            )
            session.commit()

            await process_queue_item(ingestion_log_repo, ingestion_queue_item_repo, queue_item, shared_root, rag_provider)
            session.commit()

    logger.info("Worker stopped cleanly")

def main() -> int:
    """Run the worker synchronously for CLI entrypoints."""
    return asyncio.run(run_worker())
