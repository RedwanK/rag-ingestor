import os
from .utils import AsyncMixin
from lightrag import LightRAG
from raganything import RAGAnything
from lightrag.kg.shared_storage import initialize_pipeline_status
from .llm_provider import llm_model_func
from .embed_provider import embedding_func
from .vlm_provider import vision_model_func

class RAGProvider(AsyncMixin) : 
    light_rag = None
    rag_anything = None
    
    async def __ainit__(self, rag_storage_dir = "rag_storage"):
        if os.path.exists(rag_storage_dir) and os.listdir(rag_storage_dir):
            print("✅ Found existing LightRAG instance, loading...")
        else:
            print("❌ No existing LightRAG instance found, will create new one")
        
        lightrag_instance = LightRAG(
            working_dir=rag_storage_dir,
            llm_model_func=llm_model_func,
            embedding_func=embedding_func(3072, 8192)
        )

        await lightrag_instance.initialize_storages()
        await initialize_pipeline_status()

        self.light_rag = lightrag_instance
        self.rag_anything = RAGAnything(
            lightrag=lightrag_instance,  # Pass existing LightRAG instance
            vision_model_func=vision_model_func,
        )
        