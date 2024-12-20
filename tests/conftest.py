"""Root conftest.py for all test fixtures."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from datetime import datetime, UTC
from click.testing import CliRunner
from consensus_engine.config.round_config import ROUND_SEQUENCE

class MockLLM:
    """Mock LLM for testing."""
    def __init__(self, name: str, confidence: float = 0.8):
        self.name = name
        self.confidence = confidence
        self.api_key = "mock-key"
        self._response_index = 0

    async def generate_response(self, prompt: str) -> str:
        response = f"""
UNDERSTANDING: Test understanding from {self.name} in round {self._response_index}
CONSTRAINTS: Test constraints in round {self._response_index}
INITIAL_POSITION: Test position in round {self._response_index}
CONFIDENCE: {self.confidence}
"""
        self._response_index = (self._response_index + 1) % len(ROUND_SEQUENCE)
        return response

@pytest.fixture
def mock_llms():
    """Create a list of mock LLMs."""
    return [
        MockLLM("TestLLM1"),
        MockLLM("TestLLM2")
    ]

class MockDBSession:
    """Mock database session."""
    def __init__(self):
        self.discussions = []
        self.rounds = []
        self.responses = []
        self.query = MagicMock()
        
    def add(self, obj):
        """Mock add method."""
        if hasattr(obj, '__tablename__'):
            if obj.__tablename__ == 'discussions':
                obj.id = len(self.discussions) + 1
                self.discussions.append(obj)
            elif obj.__tablename__ == 'rounds':
                obj.id = len(self.rounds) + 1
                self.rounds.append(obj)
            elif obj.__tablename__ == 'responses':
                obj.id = len(self.responses) + 1
                self.responses.append(obj)
    
    def commit(self):
        """Mock commit."""
        pass
    
    def close(self):
        """Mock close."""
        pass

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MockDBSession()

@pytest.fixture
def mock_engine(mock_llms, mock_db_session):
    """Create a mock consensus engine."""
    engine = MagicMock()
    engine.llms = mock_llms
    engine.db = mock_db_session
    
    # Create synchronous mock responses
    mock_responses = {
        llm.name: f"""
UNDERSTANDING: Test understanding from {llm.name}
CONSTRAINTS: Test constraints
INITIAL_POSITION: Test position
CONFIDENCE: {llm.confidence}
"""
        for llm in mock_llms
    }
    
    engine.discuss = AsyncMock(return_value={
        "consensus": "Test consensus",
        "individual_responses": mock_responses
    })
    return engine

@pytest.fixture
def cli_runner():
    """Create a Click CLI runner."""
    return CliRunner()

@pytest.fixture
def mock_loop():
    """Create a mock event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()