from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .config import get_rag_storage_dir
from .db import create_schema
from .services import RAGProvider
from .worker import run_worker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest sources into the local LightRAG store or run the queue worker.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    single = subparsers.add_parser("single", help="Ingest a single file or directory")
    single.add_argument(
        "source",
        type=Path,
        help="File or directory to ingest.",
    )
    single.add_argument(
        "--storage-dir",
        type=Path,
        default=get_rag_storage_dir(),
        help="Target directory for LightRAG storage (default: RAG_STORAGE_DIR)",
    )

    worker = subparsers.add_parser("worker", help="Run synchronized ingestion worker")
    worker.add_argument(
        "--poll-interval",
        type=float,
        default=None,
        help="Polling interval in seconds when queue is empty",
    )

    subparsers.add_parser("init-db", help="Create ingestion database schema")

    return parser


async def ingest_single(source_path: Path, storage_dir: Path) -> int:
    if not source_path.exists():
        raise FileNotFoundError(f"Source '{source_path}' does not exist.")

    rag = await RAGProvider(storage_dir)

    await rag.rag_anything.process_document_complete(
        file_path=source_path,
    )

    print("Great Success")
    return 0


async def ingest(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "single":
        return await ingest_single(args.source, args.storage_dir)

    if args.command == "worker":
        await run_worker(poll_interval=args.poll_interval)
        return 0

    if args.command == "init-db":
        create_schema()
        print("Database schema created")
        return 0

    parser.error("Unknown command")


def main() -> int:
    return asyncio.run(ingest())

