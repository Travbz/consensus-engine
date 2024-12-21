"""Mock clients for testing."""
from unittest.mock import AsyncMock, MagicMock
from .responses import (
    get_mock_openai_response,
    get_mock_anthropic_response,
    get_mock_gemini_response
)

class MockAsyncOpenAI:
    def __init__(self):
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        self.chat.completions.create = AsyncMock(return_value=get_mock_openai_response())

class MockAsyncAnthropic:
    def __init__(self):
        self.messages = MagicMock()
        self.messages.create = AsyncMock(return_value=get_mock_anthropic_response())

class MockGemini:
    def __init__(self):
        self.generate_content_async = AsyncMock(return_value=get_mock_gemini_response())