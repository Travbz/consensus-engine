"""OpenAI model implementation."""
from typing import Dict, Optional
from openai import AsyncOpenAI
import logging
from .base import BaseLLM
from ..config.settings import MODEL_CONFIGS

logger = logging.getLogger(__name__)

class OpenAILLM(BaseLLM):
    def __init__(
        self, 
        api_key: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        system_prompt: str = None
    ):
        # Get OpenAI config from settings
        openai_config = MODEL_CONFIGS["openai"]
        
        super().__init__(
            api_key=api_key,
            model=model or openai_config["model"],
            temperature=temperature or openai_config["temperature"],
            max_tokens=max_tokens or openai_config["max_tokens"],
            system_prompt=system_prompt or openai_config["system_prompt"]
        )
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def generate_response(self, prompt: str) -> str:
        """Generate a response including confidence score."""
        try:
            logger.info(f"Getting response from OpenAI ({self.model})")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            raise
    
    @property
    def name(self) -> str:
        return "OpenAI"