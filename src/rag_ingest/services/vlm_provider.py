import os
from lightrag.llm.openai import openai_complete
from lightrag.llm.ollama import ollama_model_complete
from dotenv import load_dotenv
from .llm_provider import llm_model_func

load_dotenv()

def vision_model_func(
        prompt, system_prompt=None, history_messages=[], image_data=None, messages=None, **kwargs
    ):
        # If messages format is provided (for multimodal VLM enhanced query), use it directly
        if messages:
            return openai_complete(
                os.getenv("LLM_MODEL"),
                "",
                system_prompt=None,
                history_messages=[],
                messages=messages,
                api_key=os.getenv("OPENAI_API_KEY"),
                **kwargs,
            )
        # Traditional single image format
        elif image_data:
            return openai_complete(
                 os.getenv("LLM_MODEL"),
                "",
                system_prompt=None,
                history_messages=[],
                messages=[
                    {"role": "system", "content": system_prompt}
                    if system_prompt
                    else None,
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                },
                            },
                        ],
                    }
                    if image_data
                    else {"role": "user", "content": prompt},
                ],
                api_key=os.getenv("OPENAI_API_KEY"),
                **kwargs,
            )
        # Pure text format
        else:
            return llm_model_func(prompt, system_prompt, history_messages, **kwargs)

def vision_model_func_bck(
        prompt, system_prompt=None, history_messages=[], image_data=None, messages=None, **kwargs
    ):
        # If messages format is provided (for multimodal VLM enhanced query), use it directly
        if messages:
            return ollama_model_complete(
                "",
                system_prompt=None,
                history_messages=[],
                messages=messages,
                **kwargs,
            )
        # Traditional single image format
        elif image_data:
            return ollama_model_complete(
                "",
                system_prompt=None,
                history_messages=[],
                messages=[
                    {"role": "system", "content": system_prompt}
                    if system_prompt
                    else None,
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                },
                            },
                        ],
                    }
                    if image_data
                    else {"role": "user", "content": prompt},
                ],
                **kwargs,
            )
        # Pure text format
        else:
            return llm_model_func(prompt, system_prompt, history_messages, **kwargs)
