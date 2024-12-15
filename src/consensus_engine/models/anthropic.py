"""Anthropic model implementation."""
from typing import Dict, Optional
from anthropic import AsyncAnthropic
import logging
from .base import BaseLLM
from ..config.settings import MODEL_CONFIGS

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
        """Generate a response including confidence score."""
        try:
            logger.info(f"Getting response from Anthropic ({self.model})")
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                system=self.system_prompt,
                temperature=self.temperature
            )
            
            return response.content[0].text

        except Exception as e:
            logger.error(f"Error generating Anthropic response: {e}")
            raise
    
    @property
    def name(self) -> str:
        return "Anthropic"