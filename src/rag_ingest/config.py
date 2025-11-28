from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(name, default)


def get_database_url() -> str:
    host = get_env("DB_HOST", "localhost")
    port = get_env("DB_PORT", "3306")
    user = get_env("DB_USER", "root")
    password = get_env("DB_PASSWORD", "")
    database = get_env("DB_NAME", "rag_manager")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


def get_shared_storage_dir() -> Path:
    return Path(get_env("SHARED_STORAGE_DIR", "shared_storage")).resolve()


def get_rag_storage_dir() -> Path:
    return Path(get_env("RAG_STORAGE_DIR", "rag_storage")).resolve()


def get_poll_interval_seconds() -> float:
    return float(get_env("INGESTOR_POLL_INTERVAL", 5))


def get_processing_timeout_seconds() -> float:
    return float(get_env("INGESTOR_PROCESSING_TIMEOUT", 3600))
