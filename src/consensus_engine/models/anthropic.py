"""Anthropic model implementation."""
from typing import Dict, Optional
from anthropic import AsyncAnthropic
import logging
from .base import BaseLLM
from ..config.settings import ANTHROPIC_CONFIG, DELIBERATION_PROMPT

logger = logging.getLogger(__name__)

class AnthropicLLM(BaseLLM):
    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model or ANTHROPIC_CONFIG["model"])
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def generate_response(self, prompt: str) -> str:
        logger.info(f"Getting response from Anthropic ({self.model})")
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=ANTHROPIC_CONFIG["max_tokens"],
            messages=[{
                "role": "user",
                "content": prompt
            }],
            system=ANTHROPIC_CONFIG["system_prompt"],
            temperature=ANTHROPIC_CONFIG["temperature"]
        )
        return response.content[0].text
    
    async def deliberate(self, prompt: str, responses: Dict[str, str]) -> str:
        logger.info("Anthropic deliberating on responses")
        deliberation_prompt = (
            f"Original prompt: {prompt}\n\n"
            "Responses:\n"
        )
        
        for llm_name, response in responses.items():
            deliberation_prompt += f"\n{llm_name}: {response}\n"
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=ANTHROPIC_CONFIG["max_tokens"],
            messages=[{
                "role": "user",
                "content": deliberation_prompt
            }],
            system=DELIBERATION_PROMPT,
            temperature=ANTHROPIC_CONFIG["temperature"]
        )
        return response.content[0].text
    
    @property
    def name(self) -> str:
        return "Anthropic"