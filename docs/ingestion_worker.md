# Synchronized ingestion worker

The ingestor now mirrors the RAG manager queue and processes files directly from the shared storage folder.

## Configuration

The worker reads its configuration from environment variables (see `.env.dist` for a full list):

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`: connection details for the shared MySQL database.
- `SHARED_STORAGE_DIR`: base directory where the RAG manager writes uploaded files (default: `shared_storage`).
- `RAG_STORAGE_DIR`: LightRAG working directory (default: `rag_storage`).
- `INGESTOR_POLL_INTERVAL`: seconds to sleep when no queued job is available (default: `5`).
- `INGESTOR_PROCESSING_TIMEOUT`: timeout in seconds after which `processing` jobs are reset to `queued` (default: `3600`).

## Database setup

Create the ingestion tables in the configured database:

```bash
rag-ingest init-db
```

The schema defines `document_nodes`, `ingestion_queue_items`, and `ingestion_logs` with an index on `(status, created_at)` to speed up queue lookups.

## Running the worker

Launch the synchronized worker instead of the one-shot CLI:

```bash
rag-ingest worker --poll-interval 2
```

Behaviour:

1. Exit immediately if another job is already marked `processing` to enforce single-worker concurrency.
2. Reset stale `processing` jobs whose `started_at` is older than the configured timeout back to `queued` and log the recovery.
3. Poll for the next `queued` job ordered by `created_at`; sleep when none is found.
4. Reserve the job (`processing`, `startedAt`, log entry), resolve its `storage_path` relative to `SHARED_STORAGE_DIR`, and ingest via LightRAG (`RAGProvider`).
5. On success: mark `indexed`, set `endedAt`, and save a success message; on failure: mark `failed`; on missing files: mark `download_failed`. Each transition adds an `IngestionLog` entry.
6. Handle SIGINT/SIGTERM to stop cleanly between jobs without leaving inconsistent statuses.

## Robust recovery

The timeout-based reset strategy re-queues any job stuck in `processing` beyond `INGESTOR_PROCESSING_TIMEOUT`. Each reset is logged with a `warning` level entry so operators can monitor unexpected restarts.
