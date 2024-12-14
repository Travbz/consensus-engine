"""Base class for LLM implementations."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLM(ABC):
    """Base class for LLM implementations."""
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Generate a response for the given prompt."""
        pass
    
    @abstractmethod
    async def deliberate(self, prompt: str, responses: Dict[str, str]) -> str:
        """Deliberate on the responses from other LLMs and provide feedback."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the LLM provider."""
        pass