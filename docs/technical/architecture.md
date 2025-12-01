# Architecture technique

## Vue d'ensemble

Le projet fournit un outil d'ingestion RAG basé sur LightRAG et RAGAnything. Deux modes principaux sont proposés :

- **Ingestion ponctuelle** via `rag-ingest single` qui lit un fichier ou un dossier et déclenche directement le pipeline LightRAG.
- **Worker synchronisé** via `rag-ingest worker` qui interroge une file d'ingestion MySQL alimentée par un manager externe, réserve le prochain job, ingère le fichier partagé puis journalise le résultat.

```
CLI / Manager ---> File MySQL (ingestion_queue_item)
                        |                
                        v                
                Worker d'ingestion -----+---> LightRAG / RAGAnything
                        ^                
                        |                
             Logs (ingestion_log)
```

## Modules principaux

- `src/rag_ingest/ingestor.py` : CLI légère pour l'ingestion ponctuelle.
- `src/rag_ingest/worker.py` : boucle asynchrone qui pilote la file d'ingestion et déclenche l'ingestion LightRAG.
- `src/rag_ingest/entity` : modèles SQLAlchemy (`DocumentNode`, `IngestionQueueItem`, `IngestionLog`, `QueueStatus`).
- `src/rag_ingest/repository` : accès aux données (sélection du prochain job, réservations, mises à jour d'état, ajout de logs).
- `src/rag_ingest/services` : adaptation LightRAG (`RAGProvider`) et wrappers de modèles (LLM, embeddings, VLM) basés sur les variables d'environnement.
- `src/rag_ingest/orm` : configuration base de données, moteur SQLAlchemy et création du schéma.

## Flux d'ingestion ponctuelle

1. `ingestor.py` parse les arguments (`source`, `--storage-dir`).
2. `RAGProvider` initialise LightRAG avec les fonctions LLM/embedding configurées.
3. `rag_anything.process_document_complete` traite le fichier et écrit les artefacts dans `rag_storage`.

## Flux du worker synchronisé

1. Boucle principale (`run_worker`) :
   - Charge les paramètres (`shared_root`, `rag_storage_dir`, intervalles) depuis `.env` via `Config`.
   - Initialise `RAGProvider` et installe des gestionnaires de signaux pour un arrêt propre.
2. À chaque itération :
   - Réinitialise les jobs `processing` trop anciens en `queued`.
   - Vérifie s'il existe déjà un job en cours pour éviter le travail concurrent.
   - Réserve le prochain job `queued` (ordre `created_at`), journalise la réservation puis commite.
   - Résout le chemin partagé (`shared_root / storage_path`) et lance `process_queue_item`.
3. `process_queue_item` :
   - Vérifie la présence du fichier ; enregistre une erreur et marque le job `failed` si absent.
   - Appelle `rag_anything.process_document_complete` ; marque `indexed` et ajoute un log `info` en cas de succès.
   - Capture les exceptions, passe le job en `failed` et trace l'erreur.

## Configuration et dépendances

- Variables chargées via `.env` (ex : `LLM_MODEL`, `EMBEDDING_MODEL`, `DB_*`, `SHARED_STORAGE_DIR`, `RAG_STORAGE_DIR`).
- Fonction d'embedding basée sur Ollama (`ollama_embed`), LLM par défaut via OpenAI (`openai_complete_if_cache`), VLM via OpenAI (`openai_complete`).
- Le schéma SQL est créé grâce à `create_schema` dans `src/rag_ingest/orm/db.py`.

## Stockage et persistence

- **Base de données** : MySQL (ou compatible) pour la file `ingestion_queue_item` et les journaux `ingestion_log`.
- **Système de fichiers** :
  - `SHARED_STORAGE_DIR` : emplacement partagé où le manager dépose les fichiers.
  - `RAG_STORAGE_DIR` : stockage LightRAG local utilisé par le worker et l'ingestor ponctuel.
