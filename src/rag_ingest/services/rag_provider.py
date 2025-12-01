from __future__ import annotations

"""Factory for asynchronously initializing LightRAG and RAGAnything providers."""

import os

from lightrag import LightRAG
from lightrag.kg.shared_storage import initialize_pipeline_status
from raganything import RAGAnything

from .embed_provider import embedding_func
from .llm_provider import llm_model_func
from .utils import AsyncMixin
from .vlm_provider import vision_model_func


class RAGProvider(AsyncMixin):
    light_rag = None
    rag_anything = None

    async def __ainit__(self, rag_storage_dir):
        """Lazily boot LightRAG storages and hydrate the RAGAnything wrapper."""
        if os.path.exists(rag_storage_dir) and os.listdir(rag_storage_dir):
            print("✅ Found existing LightRAG instance, loading...")
        else:
            print("❌ No existing LightRAG instance found, will create new one")

        lightrag_instance = LightRAG(
            working_dir=rag_storage_dir,
            llm_model_name=os.getenv("LLM_MODEL"),
            llm_model_func=llm_model_func,
            embedding_func=embedding_func(),
        )

        await lightrag_instance.initialize_storages()
        await initialize_pipeline_status()

        self.light_rag = lightrag_instance
        self.rag_anything = RAGAnything(
            lightrag=lightrag_instance,  # Pass existing LightRAG instance
            vision_model_func=vision_model_func,
        )
