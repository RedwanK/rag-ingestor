from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

class Config(): 
    def get_database_url() -> str:
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3306")
        user = os.getenv("DB_USER", "root")
        password = os.getenv("DB_PASSWORD", "")
        database = os.getenv("DB_NAME", "rag-manager")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


    def get_shared_storage_dir() -> Path:
        return Path(os.getenv("SHARED_STORAGE_DIR", "shared_storage")).resolve()


    def get_rag_storage_dir() -> Path:
        return Path(os.getenv("RAG_STORAGE_DIR", "rag_storage")).resolve()


    def get_poll_interval_seconds() -> float:
        return float(os.getenv("INGESTOR_POLL_INTERVAL", 5))


    def get_processing_timeout_seconds() -> float:
        return float(os.getenv("INGESTOR_PROCESSING_TIMEOUT", 3600))
