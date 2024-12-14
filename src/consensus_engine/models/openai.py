"""OpenAI model implementation."""
from typing import Dict, Optional
from openai import AsyncOpenAI
import logging
from .base import BaseLLM
from ..config.settings import OPENAI_CONFIG, DELIBERATION_PROMPT

logger = logging.getLogger(__name__)

class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model or OPENAI_CONFIG["model"])
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def generate_response(self, prompt: str) -> str:
        logger.info(f"Getting response from OpenAI ({self.model})")
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "system",
                "content": OPENAI_CONFIG["system_prompt"]
            }, {
                "role": "user",
                "content": prompt
            }],
            temperature=OPENAI_CONFIG["temperature"],
            max_tokens=OPENAI_CONFIG["max_tokens"]
        )
        return response.choices[0].message.content
    
    async def deliberate(self, prompt: str, responses: Dict[str, str]) -> str:
        logger.info("OpenAI deliberating on responses")
        deliberation_prompt = (
            f"Original prompt: {prompt}\n\n"
            "Responses:\n"
        )
        
        for llm_name, response in responses.items():
            deliberation_prompt += f"\n{llm_name}: {response}\n"
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "system",
                "content": DELIBERATION_PROMPT
            }, {
                "role": "user",
                "content": deliberation_prompt
            }],
            temperature=OPENAI_CONFIG["temperature"],
            max_tokens=OPENAI_CONFIG["max_tokens"]
        )
        return response.choices[0].message.content
    
    @property
    def name(self) -> str:
        return "OpenAI"