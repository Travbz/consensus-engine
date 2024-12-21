"""Test fixtures and configuration."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from consensus_engine.database.models import Base, Discussion
from consensus_engine.models.base import BaseLLM
from tests.mocks.clients import MockAsyncOpenAI, MockAsyncAnthropic, MockGemini
from tests.mocks.responses import get_mock_llm_response

class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    def __init__(self, name="MockLLM", confidence=0.8):
        super().__init__(
            api_key="test-key",
            model="test-model",
            temperature=0.7,
            max_tokens=2000
        )
        self._name = name
        self._confidence = confidence
        self._mock_response_text = None
        self._round = None

    @property
    def name(self) -> str:
        return self._name

    async def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate mock response matching the current round format."""
        if "PRE_FLOP" in prompt:
            self._round = "PRE_FLOP"
            response = f"""UNDERSTANDING: Test understanding
                         CONSTRAINTS: Test constraints
                         INITIAL_POSITION: Test position from {self._name}
                         CONFIDENCE: {self._confidence}"""
        elif "FLOP" in prompt:
            self._round = "FLOP"
            response = f"""FORMAT_PROPOSAL: Test format proposal
                         INITIAL_SOLUTION: Test solution from {self._name}
                         RATIONALE: Test rationale
                         CONFIDENCE: {self._confidence}"""
        elif "TURN" in prompt:
            self._round = "TURN"
            response = f"""FORMAT_AGREEMENT: Test agreement
                         REFINED_SOLUTION: Test refinement from {self._name}
                         FORMAT_IMPROVEMENTS: Test improvements
                         CONFIDENCE: {self._confidence}"""
        elif "RIVER" in prompt:
            self._round = "RIVER"
            response = f"""IMPLEMENTATION: Test implementation from {self._name}
                         CONFIDENCE: {self._confidence}"""
        else:
            self._round = "SHOWDOWN"
            response = f"""IMPLEMENTATION: Final solution from {self._name}
                         CONFIDENCE: {self._confidence}"""
        
        self._mock_response_text = response
        return response

    def get_confidence(self) -> float:
        """Get confidence score."""
        return self._confidence

    @property
    def last_response(self) -> str:
        """Get the last generated response."""
        return self._mock_response_text

    @property
    def current_round(self) -> str:
        """Get the current round."""
        return self._round

class MockDBSession:
    """Mock database session with discussion tracking."""
    def __init__(self):
        self.discussions = []
        self._query = MagicMock()
        self._query.filter = MagicMock(return_value=self._query)
        self._query.first = MagicMock(return_value=None)
        self._query.all = MagicMock(return_value=self.discussions)
        self._query.get = MagicMock(side_effect=self.get_discussion)

    def add(self, obj):
        if isinstance(obj, Discussion):
            self.discussions.append(obj)

    def commit(self):
        pass

    def close(self):
        pass

    def get_discussion(self, id):
        for discussion in self.discussions:
            if discussion.id == id:
                return discussion
        return None

    def query(self, *args, **kwargs):
        return self._query

@pytest.fixture
def cli_runner():
    """Fixture for testing CLI."""
    return CliRunner()

@pytest.fixture
def mock_engine():
    """Fixture for mocking ConsensusEngine."""
    engine = MagicMock()
    engine.discuss = AsyncMock()
    return engine

@pytest.fixture
def mock_db_session():
    """Fixture for mocking database session."""
    return MockDBSession()

@pytest.fixture
def mock_openai_client():
    """Fixture for mocking OpenAI client."""
    return MockAsyncOpenAI()

@pytest.fixture
def mock_anthropic_client():
    """Fixture for mocking Anthropic client."""
    return MockAsyncAnthropic()

@pytest.fixture
def mock_gemini_client():
    """Fixture for mocking Gemini client."""
    return MockGemini()

@pytest.fixture
def mock_llms():
    """Fixture for mocking multiple LLMs."""
    return [
        MockLLM("MockLLM1", confidence=0.9),
        MockLLM("MockLLM2", confidence=0.8),
        MockLLM("MockLLM3", confidence=0.7)
    ]

@pytest.fixture
def mock_model_loader(mock_llms):
    """Fixture for mocking ModelLoader."""
    mock = MagicMock()
    mock.load_models = MagicMock(return_value=mock_llms)
    mock.validate_models = MagicMock(return_value=True)
    return mock

@pytest.fixture
def mock_llm():
    """Fixture for mocking a generic LLM."""
    return MockLLM()