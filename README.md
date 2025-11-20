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
   rag-ingest <fichier_ou_dossier> --storage-dir rag_storage
   # ex
   rag-ingest assets/01_offre_maintenance_predictive.pdf --storage-dir rag_storage
   ```

3. Les documents sont traités par `LightRAG` via `RAGAnything`, puis indexés dans `rag_storage/`.
4. Interroger ensuite le store via LightRAG, OpenWebUI ou ton API/outil préféré.

---

Besoin d’une doc complémentaire (ex. déploiement en prod, configuration avancée des modèles) ? Ajoute une section dédiée ou crée un fichier `docs/`.
