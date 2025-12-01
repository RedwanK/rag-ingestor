from __future__ import annotations

"""Environment-backed configuration helpers for database and storage paths."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

class Config(): 
    """Provide typed accessors for environment-driven configuration values."""

    def get_database_url() -> str:
        """Build the SQLAlchemy connection URL from environment variables."""
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3306")
        user = os.getenv("DB_USER", "root")
        password = os.getenv("DB_PASSWORD", "")
        database = os.getenv("DB_NAME", "rag-manager")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


    def get_shared_storage_dir() -> Path:
        """Absolute path to the shared storage directory used to read source files."""
        return Path(os.getenv("SHARED_STORAGE_DIR", "shared_storage")).resolve()


    def get_rag_storage_dir() -> Path:
        """Absolute path to the LightRAG storage directory."""
        return Path(os.getenv("RAG_STORAGE_DIR", "rag_storage")).resolve()


    def get_poll_interval_seconds() -> float:
        """Polling interval in seconds for the ingestion worker loop."""
        return float(os.getenv("INGESTOR_POLL_INTERVAL", 5))


    def get_processing_timeout_seconds() -> float:
        """Maximum time in seconds a job may remain in processing before being reset."""
        return float(os.getenv("INGESTOR_PROCESSING_TIMEOUT", 3600))
