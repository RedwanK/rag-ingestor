# Quickstart

Installer le projet en mode dev :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Installation (Linux & macOS)

### 1. Prérequis

- `git`
- `python >= 3.12`
- Accès à une clé API OpenAI
- Accès sudo (Linux) pour installer un service
- (Recommandé) Docker / Docker Desktop pour OpenWebUI

### 2. Installer Ollama

Ollama est utilisé pour générer les embeddings (via `ollama_embed`).

**Linux**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
ollama serve &
ollama pull embeddinggemma:300m
```

**macOS**

```bash
brew install ollama     # ou utiliser l'installeur officiel
ollama pull embeddinggemma:300m
```

### 3. Cloner et installer le projet dans un venv

```bash
git clone <URL_DU_REPO> rag-ingestor
cd rag-ingestor
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 4. Configurer l’environnement (`.env`)

```bash
cp .env.dist .env
```

Dans `.env`, renseigner au minimum :

- `OPENAI_API_KEY=<ta_cle_api>`
- `OPENAI_INGESTION_MODEL=<modele_openai>`
- `OPENAI_EMBEDDING_MODEL=<modele_embedding_openai>` (si utilisé)
- `LLM_MODEL` et `LLM_BINDING` (pour LightRAG)
- Variables Ollama :
  - `EMBEDDING_MODEL="embeddinggemma:300m"`
  - `EMBEDDING_DIM=768`
  - `EMBEDDING_BINDING=ollama`
  - `EMBEDDING_BINDING_HOST=http://localhost:11434`

Toutes les variables disponibles sont visibles dans `.env.dist` et les fichiers `src/rag_ingest/services/*.py`.

Variables supplémentaires pour le gestionnaire d'ingestion synchronisé :

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` : base MySQL partagée avec le manager.
- `SHARED_STORAGE_DIR` : répertoire commun où le manager dépose les fichiers en attente (défaut : `shared_storage`).
- `RAG_STORAGE_DIR` : répertoire LightRAG (défaut : `rag_storage`).
- `INGESTOR_POLL_INTERVAL` : intervalle en secondes entre deux sondes quand la file est vide (défaut : `5`).
- `INGESTOR_PROCESSING_TIMEOUT` : délai en secondes avant de remettre un job `processing` en `queued` (défaut : `3600`).

### 5. Installer LightRAG comme service (Linux)

Vérifier que `lightrag-server` est disponible :

```bash
.venv/bin/lightrag-server --help
```

Adapter `lightrag.service` si nécessaire (chemins, env). Exemple :

```ini
[Unit]
Description=LightRag instance for custom RAG

[Service]
Environment="PATH=/var/www/rag-ingestor/.venv/bin"
WorkingDirectory=/var/www/rag-ingestor
ExecStart=/var/www/rag-ingestor/.venv/bin/lightrag-server

[Install]
WantedBy=multi-user.target
```

Installer et activer le service :

```bash
sudo cp lightrag.service /etc/systemd/system/lightrag.service
sudo systemctl daemon-reload
sudo systemctl enable --now lightrag
systemctl status lightrag
```

Sur macOS (pas de systemd), lancer simplement :

```bash
source .venv/bin/activate
lightrag-server
```

ou créer un service `launchd` équivalent.

### 6. Installer OpenWebUI

OpenWebUI offre une interface web pour Ollama / RAG. Déploiement recommandé via Docker :

```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

Puis ouvrir `http://localhost:3000` pour configurer Ollama, les clés API, etc.

### 7. Ingestion de documents

1. S’assurer que :
   - `.venv` est activé
   - `.env` est configuré
   - le serveur LightRAG tourne (service `lightrag` ou `lightrag-server`)
2. Lancer l’ingestion :

   ```bash
   rag-ingest single <fichier_ou_dossier> --storage-dir rag_storage
   # ex
   rag-ingest single assets/01_offre_maintenance_predictive.pdf --storage-dir rag_storage
   ```

3. Les documents sont traités par `LightRAG` via `RAGAnything`, puis indexés dans `rag_storage/`.
4. Interroger ensuite le store via LightRAG, OpenWebUI ou ton API/outil préféré.

### 8. Worker d’ingestion synchronisé

Pour ingérer automatiquement les fichiers planifiés par le manager via MySQL :

```bash
rag-ingest init-db              # créer le schéma des tables d’ingestion
rag-ingest worker --poll-interval 2
```

Le worker :

- vérifie qu’aucun job n’est déjà en `processing` (un seul worker actif à la fois),
- remet en `queued` les jobs `processing` plus vieux que `INGESTOR_PROCESSING_TIMEOUT`,
- lit le prochain job `queued` ordonné par `createdAt`, le réserve (`processing` + `startedAt`),
- résout `storage_path` sous `SHARED_STORAGE_DIR`, lance l’ingestion LightRAG, puis passe le statut à `indexed`/`failed`/`download_failed` et consigne les événements dans `ingestion_logs`.

Plus de détails dans `docs/ingestion_worker.md`.

---

Besoin d’une doc complémentaire (ex. déploiement en prod, configuration avancée des modèles) ? Ajoute une section dédiée ou crée un fichier `docs/`.
