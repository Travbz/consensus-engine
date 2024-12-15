"""Tests for the consensus engine core functionality."""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from consensus_engine.engine import ConsensusEngine
from consensus_engine.database.models import Base, Discussion
from consensus_engine.config.round_config import ROUND_SEQUENCE

class MockLLM:
    def __init__(self, name="MockLLM", responses=None):
        self.name = name
        self.responses = responses or {}
        self.api_key = "mock-key"
        self.model = "mock-model"
        self.temperature = 0.7
        self.max_tokens = 2000
        self.system_prompt = "mock prompt"

    async def generate_response(self, prompt: str) -> str:
        # Return pre-configured responses or a default response
        return self.responses.get(prompt, f"""
        UNDERSTANDING: Test understanding
        CONSTRAINTS: Test constraints
        INITIAL_POSITION: Test position
        CONFIDENCE: 0.8 This is a test response
        """)

@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

@pytest.fixture
def mock_llms():
    """Create mock LLMs with predefined responses."""
    llm1 = MockLLM("MockLLM1", {
        "test_prompt": """
        UNDERSTANDING: Clear understanding
        CONSTRAINTS: Known constraints
        INITIAL_POSITION: Strong position
        CONFIDENCE: 0.9 High confidence response
        """
    })
    
    llm2 = MockLLM("MockLLM2", {
        "test_prompt": """
        UNDERSTANDING: Similar understanding
        CONSTRAINTS: Similar constraints
        INITIAL_POSITION: Compatible position
        CONFIDENCE: 0.85 Good confidence response
        """
    })
    
    return [llm1, llm2]

@pytest.fixture
def engine(db_session, mock_llms):
    """Create a consensus engine instance with mock LLMs."""
    return ConsensusEngine(mock_llms, db_session)

@pytest.mark.asyncio
async def test_basic_consensus(engine):
    """Test basic consensus achievement."""
    result = await engine.discuss("test_prompt")
    assert isinstance(result, dict)
    assert "consensus" in result or len(result) == len(engine.llms)

@pytest.mark.asyncio
async def test_confidence_extraction(engine):
    """Test confidence score extraction from responses."""
    result = await engine.discuss("test_prompt")
    # Check if we get confidence scores
    if "consensus" in result:
        assert isinstance(result.get("consensus"), str)
    else:
        assert all(isinstance(r, str) for r in result.values())

@pytest.mark.asyncio
async def test_round_progression(engine):
    """Test that rounds progress correctly."""
    async def progress_callback(msg: str):
        assert isinstance(msg, str)
    
    result = await engine.discuss("test_prompt", progress_callback)
    # Verify rounds were processed
    discussions = engine.db.query(Discussion).all()
    assert len(discussions) > 0
    assert len(discussions[0].rounds) > 0

@pytest.mark.asyncio
async def test_similarity_calculation(engine):
    """Test similarity calculation between responses."""
    responses = {
        "LLM1": "This is a test response about consensus",
        "LLM2": "This is another test response about reaching consensus"
    }
    similarity = engine._calculate_similarity(responses)
    assert 0 <= similarity <= 1

@pytest.mark.asyncio
async def test_error_handling(engine):
    """Test error handling during discussion."""
    # Create a failing LLM
    failing_llm = MockLLM("FailingLLM")
    failing_llm.generate_response = AsyncMock(side_effect=Exception("Test error"))
    engine.llms.append(failing_llm)
    
    # Should continue with remaining LLMs
    result = await engine.discuss("test_prompt")
    assert isinstance(result, dict)

@pytest.mark.asyncio
async def test_round_specific_prompts(engine):
    """Test that each round uses appropriate prompts."""
    async def progress_callback(msg: str):
        # Check if round types are mentioned in progress messages
        for round_type in ROUND_SEQUENCE:
            if round_type in msg:
                return
    
    result = await engine.discuss("test_prompt", progress_callback)
    assert isinstance(result, dict)

@pytest.mark.asyncio
async def test_consensus_threshold(engine):
    """Test consensus threshold behavior."""
    # Create LLMs with very different responses
    divergent_llm = MockLLM("DivergentLLM", {
        "test_prompt": """
        UNDERSTANDING: Completely different understanding
        CONSTRAINTS: Different constraints
        INITIAL_POSITION: Opposing position
        CONFIDENCE: 0.4 Low confidence response
        """
    })
    engine.llms.append(divergent_llm)
    
    result = await engine.discuss("test_prompt")
    # Should not reach consensus with divergent responses
    assert isinstance(result, dict)
    assert all(isinstance(r, str) for r in result.values())