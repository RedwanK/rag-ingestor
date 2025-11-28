# RAG manager integration – implementation backlog

## Data synchronisation

- [ ] Implement SQLAlchemy models for `DocumentNode`, `IngestionQueueItem`, and `IngestionLog` matching the functional spec (fields, types, relations) #backend #db #rag-manager
- [ ] Configure shared MySQL connection in the ingestor (env vars, SQLAlchemy engine/session factory) to use the same database as the manager #backend #db #config
- [ ] Create the MySQL schema or migrations for the ingestion tables used by the ingestor (including indexes on `status` and `createdAt`) #backend #db
- [ ] Implement repository helpers to read/write queue items and logs (get next `queued` by `createdAt`, check for existing `processing`, update statuses and timestamps) #backend #db #ingestion

## Files synchronisation

- [ ] Read the shared storage base directory from `.env` and expose it to the ingestion worker configuration #backend #config #ingestion
- [ ] Resolve `IngestionQueueItem.storage_path` into an absolute path under the shared directory before ingestion #backend #ingestion
- [ ] Handle missing or unreadable files by marking the job `download_failed` and inserting an appropriate `IngestionLog` entry #backend #ingestion #error-handling

## Synchronized ingestion worker

- [ ] Implement a long-running ingestion worker that polls MySQL for jobs instead of only ingesting a single file from the CLI #backend #ingestion
- [ ] Implement the polling loop with a configurable sleep interval when no `queued` job is available #backend #ingestion
- [ ] Before reserving any job, check for an existing `processing` `IngestionQueueItem` and exit early if found to enforce single-job concurrency #backend #ingestion #concurrency
- [ ] When no `processing` job exists, fetch the next `queued` `IngestionQueueItem` ordered by `createdAt` #backend #ingestion
- [ ] Reserve the selected job by switching its status to `processing` and setting `startedAt` #backend #ingestion
- [ ] Integrate the LightRAG ingestion pipeline (`RAGProvider`) to process the file referenced by the queue item #backend #ingestion #lightrag
- [ ] On successful ingestion, update the job to status `indexed`, set `endedAt`, and populate `ragMessage` with a meaningful outcome message #backend #ingestion
- [ ] On ingestion failure, update the job to status `failed`, set `endedAt`, and log error details in `IngestionLog` #backend #ingestion #error-handling
- [ ] Ensure the worker stops cleanly on shutdown (signals/interrupt) without leaving inconsistent statuses in the queue #backend #ingestion

## Robustness and monitoring

- [ ] Define and document a strategy for handling stale `processing` items after crash or timeout to satisfy the “robust recovery” requirement from the spec #backend #ingestion #reliability
- [ ] Implement the chosen recovery strategy (e.g. reset timed-out `processing` jobs back to `queued` and log the event) #backend #ingestion #reliability
- [ ] Add logging/metrics around the ingestion loop (poll events, job start/end, failures, early exits due to `processing` job) #backend #ingestion #observability

## Tests and documentation

- [ ] Add unit/integration tests for the database layer (queue selection by `status` and `createdAt`, status transitions, log insertion) #tests #backend #ingestion
- [ ] Add tests for the ingestion worker loop covering single-job concurrency and status transitions (`queued` → `processing` → `indexed`/`failed`/`download_failed`) #tests #backend #ingestion
- [ ] Update developer documentation to describe configuration (.env, DB connection, shared storage directory), the ingestion worker command, and the synchronized ingestion workflow with the queue #docs #backend #ingestion
