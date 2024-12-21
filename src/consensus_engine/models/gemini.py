"""Google Gemini model implementation."""
from typing import Dict, Optional
import google.generativeai as genai
import logging
from .base import BaseLLM
from ..config.settings import MODEL_CONFIGS

logger = logging.getLogger(__name__)

class GeminiLLM(BaseLLM):
    def __init__(
        self,
        api_key: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        system_prompt: str = None
    ):
        # Get Gemini config from settings
        gemini_config = MODEL_CONFIGS["gemini"]
        
        super().__init__(
            api_key=api_key,
            model=model or gemini_config["model"],
            temperature=temperature or gemini_config["temperature"],
            max_tokens=max_tokens or gemini_config["max_tokens"],
            system_prompt=system_prompt or gemini_config["system_prompt"]
        )
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model_name=self.model)
        
        # Get Gemini-specific configurations
        self.generation_config = gemini_config.get("generation_config", {})
        self.safety_settings = gemini_config.get("safety_settings", {})
    
    async def generate_response(self, prompt: str) -> str:
        try:
            # Combine system prompt and user prompt if system prompt exists
            full_prompt = f"{self.system_prompt}\n\n{prompt}" if self.system_prompt else prompt
            
            response = await self.client.generate_content_async(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    candidate_count=self.generation_config.get("candidate_count", 1),
                    top_p=self.generation_config.get("top_p", 1),
                    top_k=self.generation_config.get("top_k", 40)
                )
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            raise

    @property
    def name(self) -> str:
        return "Gemini"