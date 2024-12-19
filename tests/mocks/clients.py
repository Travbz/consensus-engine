"""Mock clients for testing."""
from unittest.mock import AsyncMock, MagicMock

class MockAsyncOpenAI:
    """Mock OpenAI client."""
    def __init__(self):
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        self.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content="UNDERSTANDING: Test understanding\nCONFIDENCE: 0.9\n"
                )
            )]
        ))

class MockAsyncAnthropic:
    """Mock Anthropic client."""
    def __init__(self):
        self.messages = MagicMock()
        self.messages.create = AsyncMock(return_value=MagicMock(
            content=[MagicMock(
                text="UNDERSTANDING: Test understanding\nCONFIDENCE: 0.9\n"
            )]
        ))
