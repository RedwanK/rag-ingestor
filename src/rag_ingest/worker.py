from __future__ import annotations

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
from .repository import (
    get_next_queued,
    has_processing,
    log_event,
    mark_failed,
    mark_indexed,
    reset_stale_processing,
    reserve_for_processing,
)
from .services import RAGProvider

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MissingFileError(FileNotFoundError):
    """Raised when the referenced queue item file cannot be read."""


def resolve_storage_path(shared_root: Path, relative_path: str) -> Path:
    return (shared_root / relative_path).resolve()


async def process_queue_item(
    session_factory: sessionmaker,
    queue_item: IngestionQueueItem,
    shared_root: Path,
    rag_provider: RAGProvider,
) -> None:
    with session_factory() as session:
        queue_item = session.get(IngestionQueueItem, queue_item.id)
        abs_path = resolve_storage_path(shared_root, queue_item.storage_path)
        if not abs_path.exists() or not abs_path.is_file():
            logger.error("File missing or unreadable: %s", abs_path)
            mark_failed(
                session,
                queue_item,
                status=QueueStatus.download_failed,
                rag_message=f"File not found at {abs_path}",
            )
            log_event(
                session,
                ingestion_queue_item_id=queue_item.id,
                level="error",
                message=f"Unable to open file at {abs_path}",
            )
            session.commit()
            return

        try:
            await rag_provider.rag_anything.process_document_complete(file_path=abs_path)
            mark_indexed(
                session,
                queue_item,
                rag_message="Ingestion completed successfully",
            )
            log_event(
                session,
                ingestion_queue_item_id=queue_item.id,
                level="info",
                message=f"Successfully ingested {queue_item.storage_path}",
            )
            session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Ingestion failed for queue item %s", queue_item.id)
            mark_failed(
                session,
                queue_item,
                status=QueueStatus.failed,
                rag_message=str(exc),
            )
            log_event(
                session,
                ingestion_queue_item_id=queue_item.id,
                level="error",
                message=f"Failed to ingest {queue_item.storage_path}: {exc}",
            )
            session.commit()


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
            reset_ids = reset_stale_processing(session, processing_timeout)
            if reset_ids:
                session.commit()
                logger.warning("Reset %s stale jobs to queued", reset_ids)

            if has_processing(session):
                logger.info("Another worker is already processing a job; exiting")
                return

            queue_item = get_next_queued(session)
            if queue_item is None:
                session.commit()
                if exit_on_idle:
                    return
                await asyncio.sleep(poll_interval)
                continue

            reserve_for_processing(session, queue_item, started_at=datetime.now(timezone.utc))
            log_event(
                session,
                ingestion_queue_item_id=queue_item.id,
                level="info",
                message="Job reserved for processing",
            )
            session.commit()

        await process_queue_item(session_factory, queue_item, shared_root, rag_provider)

    logger.info("Worker stopped cleanly")

def main() -> int:
    return asyncio.run(run_worker())