"""Base class for LLM implementations."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLM(ABC):
    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt

    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Generate a response for the given prompt."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the LLM provider."""
        pass