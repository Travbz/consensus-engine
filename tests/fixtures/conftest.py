"""Shared test fixtures."""
import pytest
from unittest.mock import AsyncMock, MagicMock
import asyncio
from datetime import datetime, UTC
from tests.mocks.responses import (
    get_mock_llm_response,
    get_mock_openai_response,
    get_mock_anthropic_response,
    get_mock_progress_messages
)
from tests.mocks.db import MockDBSession, MockDiscussion

# LLM Fixtures
class MockLLM:
    """Mock LLM for testing."""
    def __init__(self, name="MockLLM", confidence=0.8):
        self.name = name
        self.confidence = confidence
        self.api_key = "mock-key"
        self.model = "mock-model"
        self.temperature = 0.7
        self.max_tokens = 2000
        self.system_prompt = "mock prompt"

    async def generate_response(self, prompt: str) -> str:
        return get_mock_llm_response(self.name, self.confidence)

@pytest.fixture
def mock_llms():
    """Create a list of mock LLMs."""
    return [
        MockLLM("TestLLM1"),
        MockLLM("TestLLM2")
    ]

# Database Fixtures
@pytest.fixture
def mock_db_session():
    """Create a mock database session with state management."""
    return MockDBSession()

# Engine Fixtures
@pytest.fixture
def mock_engine(mock_llms, mock_db_session):
    """Create a mock consensus engine."""
    engine = MagicMock()
    engine.llms = mock_llms
    engine.db = mock_db_session
    engine.discuss = AsyncMock(return_value={
        "consensus": "Test consensus",
        "individual_responses": {
            llm.name: get_mock_llm_response(llm.name)
            for llm in mock_llms
        }
    })
    return engine

# Progress Callback Fixtures
class AsyncCallbackTracker:
    """Tracks progress callback messages."""
    def __init__(self):
        self.messages = []
        
    async def callback(self, msg: str):
        self.messages.append(msg)
        await asyncio.sleep(0)
        
@pytest.fixture
def callback_tracker():
    """Create a progress callback tracker."""
    return AsyncCallbackTracker()

# Web Interface Fixtures
@pytest.fixture
def mock_gradio_blocks():
    """Create mock Gradio blocks."""
    mock = MagicMock()
    mock.launch = MagicMock()
    return mock

# Integration Test Markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", 
        "integration: mark test as an integration test"
    )