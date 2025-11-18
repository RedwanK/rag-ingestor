import os
from dotenv import load_dotenv
from lightrag.utils import EmbeddingFunc
from lightrag.llm.openai import openai_embed

load_dotenv()

def embedding_func(embedding_dim = 3072, max_token_size=8192):
    return EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=max_token_size,
        func=lambda texts: openai_embed(
            texts,
            model=os.getenv("OPENAI_EMBEDDING_MODEL"),
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
    )
