"""CLI entrypoint to ingest a single source into the LightRAG store."""

import argparse
import asyncio
from pathlib import Path

from .services import llm_model_func, embedding_func, vision_model_func, RAGProvider

def build_parser() -> argparse.ArgumentParser:
    """Define CLI arguments for ingesting files or directories."""
    parser = argparse.ArgumentParser(
        description="Ingest sources into the local LightRAG store."
    )
    parser.add_argument(
        "source",
        type=Path,
        help="File or directory to ingest.",
    )
    parser.add_argument(
        "--storage-dir",
        type=Path,
        default=Path("rag_storage"),
        help="Target directory for LightRAG storage (default: rag_storage).",
    )
    return parser

async def ingest(argv: list[str] | None = None) -> int:
    """Run the ingestion flow for a provided filesystem path."""
    parser = build_parser()
    args = parser.parse_args(argv)

    source_path: Path = args.source
    storage_dir: Path = args.storage_dir

    if not source_path.exists():
        parser.error(f"Source '{source_path}' does not exist.")

    rag = await RAGProvider(storage_dir)
    
    await rag.rag_anything.process_document_complete(
        file_path=source_path,
    )

    print('Great Success')

def main() -> int:
    """Synchronous wrapper to launch the async ingest coroutine."""
    return asyncio.run(ingest())
