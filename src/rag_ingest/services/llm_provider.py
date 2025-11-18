import os
from dotenv import load_dotenv
from lightrag.llm.ollama import ollama_model_complete

load_dotenv()

def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
    return ollama_model_complete(
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        **kwargs,
    )