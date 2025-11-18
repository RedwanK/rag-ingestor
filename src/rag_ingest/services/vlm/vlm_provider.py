import os
from lightrag.llm.openai import openai_complete_if_cache
from dotenv import load_dotenv
from ..llm import llm_model_func

load_dotenv()

def vision_model_func(
        prompt, system_prompt=None, history_messages=[], image_data=None, messages=None, **kwargs
    ):
        # If messages format is provided (for multimodal VLM enhanced query), use it directly
        if messages:
            return openai_complete_if_cache(
                os.getenv("OPENAI_VISION_MODEL"),
                "",
                system_prompt=None,
                history_messages=[],
                messages=messages,
                api_key=os.getenv("OPENAI_API_KEY"),
                **kwargs,
            )
        # Traditional single image format
        elif image_data:
            return openai_complete_if_cache(
                os.getenv("OPENAI_VISION_MODEL"),
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
