import os
from dotenv import load_dotenv
from lightrag.llm.openai import openai_complete_if_cache

load_dotenv()

def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
    return openai_complete_if_cache(
        os.getenv("LLM_MODEL"),
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=os.getenv("OPENAI_API_KEY"),
        **kwargs,
    )