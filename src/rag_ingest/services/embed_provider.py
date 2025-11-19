import os
from dotenv import load_dotenv
from lightrag.utils import EmbeddingFunc
from lightrag.llm.ollama import ollama_embed

load_dotenv()

def embedding_func(max_token_size=2048):
    return EmbeddingFunc(
        embedding_dim=int(os.getenv("EMBEDDING_DIM")),
        max_token_size=max_token_size,
        func=lambda texts: ollama_embed(
            texts,
            embed_model=os.getenv("EMBEDDING_MODEL"),
        ),
    )
