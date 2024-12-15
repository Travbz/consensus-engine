"""Anthropic model implementation."""
from typing import Dict, Optional
from anthropic import AsyncAnthropic
import logging
from .base import BaseLLM
from ..config.settings import MODEL_CONFIGS, DELIBERATION_PROMPT

logger = logging.getLogger(__name__)

class AnthropicLLM(BaseLLM):
    def __init__(
        self, 
        api_key: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        system_prompt: str = None
    ):
        # Get Anthropic config from settings
        anthropic_config = MODEL_CONFIGS["anthropic"]
        
        super().__init__(
            api_key=api_key,
            model=model or anthropic_config["model"],
            temperature=temperature or anthropic_config["temperature"],
            max_tokens=max_tokens or anthropic_config["max_tokens"],
            system_prompt=system_prompt or anthropic_config["system_prompt"]
        )
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def generate_response(self, prompt: str) -> str:
        logger.info(f"Getting response from Anthropic ({self.model})")
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            system=self.system_prompt,
            temperature=self.temperature
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
            max_tokens=self.max_tokens,
            messages=[{
                "role": "user",
                "content": deliberation_prompt
            }],
            system=DELIBERATION_PROMPT,
            temperature=self.temperature
        )
        return response.content[0].text
    
    @property
    def name(self) -> str:
        return "Anthropic"