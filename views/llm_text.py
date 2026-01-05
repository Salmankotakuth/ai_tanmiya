"""
LLM Text Generator (Placeholder)
--------------------------------

This module provides a clean interface function:
    generate_gpt_report(meeting_data, scores, predictions)

You can later replace the placeholder logic with:
- GPT-4 API
- Local LLM (Ollama)
- Azure OpenAI
- Together AI
etc.

For now it safely returns a formatted text summary.
"""

import logging
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger("tanmiya.views.llm_text")

deepseek_key = "lPb1F5Lqd7hhI8t2qczDb9DGQ1z5ds0T"

openai = OpenAI(api_key=deepseek_key, base_url="https://api.deepinfra.com/v1/openai")

async def generate_gpt_report(system_prompt: str, user_prompt: str) -> str:
    if not user_prompt:
        return ""

    # handling string and list inputs
    if isinstance(system_prompt, str):
        system_prompt_string = system_prompt
    else:
        system_prompt_string = " ".join(system_prompt)

    if isinstance(user_prompt, str):
        user_prompt_string = user_prompt
    else:
        user_prompt_string = " ".join(user_prompt)


    # system_prompt_string = " ".join(system_prompt)
    # user_prompt_string = " ".join(user_prompt)

    completion = openai.chat.completions.create(
        # model="deepseek-ai/DeepSeek-R1-Turbo",
        # model="deepseek-ai/DeepSeek-R1",
        model="openai/gpt-oss-120b",
        # model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        # model="Qwen/Qwen3-235B-A22B",

        messages=[
            {"role": "system", "content": system_prompt_string},
            {"role": "user", "content": user_prompt_string}
        ],
        temperature=0.7   # For reducing the creativity in the gpt prompt and getting similar response each time
    )

    if completion.choices and completion.choices[0].message:
        return completion.choices[0].message.content
    else:
        return "Error: No response from LLM"
