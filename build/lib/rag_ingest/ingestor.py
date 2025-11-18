import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
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

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    source_path: Path = args.source
    storage_dir: Path = args.storage_dir

    if not source_path.exists():
        parser.error(f"Source '{source_path}' does not exist.")
    
    print('Great Success')