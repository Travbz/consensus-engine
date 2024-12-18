"""Integration tests for the consensus engine."""
import pytest
import asyncio
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from consensus_engine.engine import ConsensusEngine
from consensus_engine.models.openai import OpenAILLM
from consensus_engine.models.anthropic import AnthropicLLM
from consensus_engine.database.models import Base, Discussion
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.fixture(scope="module")
def db_engine():
    """Create a test database engine."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(db_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def real_llms():
    """Create real LLM instances with API keys from environment."""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key or not anthropic_key:
        pytest.skip("API keys not available")
    
    return [
        OpenAILLM(openai_key),
        AnthropicLLM(anthropic_key)
    ]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_discussion_flow(db_session, real_llms):
    """Test a complete discussion flow with real LLMs."""
    engine = ConsensusEngine(real_llms, db_session)
    
    test_prompt = "What is the capital of France? Provide a clear, simple answer."
    
    result = await engine.discuss(test_prompt)
    
    # Check database state
    discussion = db_session.query(Discussion).first()
    assert discussion is not None
    assert discussion.prompt == test_prompt
    assert discussion.completed_at is not None
    
    # Check rounds were recorded
    assert len(discussion.rounds) > 0
    for round in discussion.rounds:
        assert len(round.responses) > 0
        for response in round.responses:
            assert response.llm_name in [llm.name for llm in real_llms]
            assert response.response_text is not None
            assert response.confidence_score is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_multi_discussion_isolation(db_session, real_llms):
    """Test multiple discussions don't interfere with each other."""
    engine = ConsensusEngine(real_llms, db_session)
    
    prompts = [
        "What is 2+2?",
        "What color is the sky?",
    ]
    
    results = []
    for prompt in prompts:
        result = await engine.discuss(prompt)
        results.append(result)
    
    discussions = db_session.query(Discussion).all()
    assert len(discussions) == len(prompts)
    
    # Check each discussion is properly isolated
    for disc, prompt in zip(discussions, prompts):
        assert disc.prompt == prompt
        assert len(disc.rounds) > 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_discussions(db_session, real_llms):
    """Test handling multiple concurrent discussions."""
    engine = ConsensusEngine(real_llms, db_session)
    
    prompts = [
        "What is the first month of the year?",
        "What is the last month of the year?",
        "How many months are in a year?",
    ]
    
    async def run_discussion(prompt):
        return await engine.discuss(prompt)
    
    tasks = [run_discussion(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == len(prompts)
    discussions = db_session.query(Discussion).all()
    assert len(discussions) == len(prompts)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_recovery(mock_engine, mock_db_session):
    """Test recovery from API errors."""
    # Setup mock to fail once then succeed
    mock_engine.discuss = AsyncMock(side_effect=[
        Exception("Simulated API error"),
        {
            "consensus": "Test consensus",
            "individual_responses": {
                "LLM1": "Test response 1",
                "LLM2": "Test response 2"
            }
        }
    ])
    
    with patch('consensus_engine.engine.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.engine.ConsensusEngine', return_value=mock_engine):
        # Your test logic here
        pass

@pytest.mark.integration
@pytest.mark.asyncio
async def test_long_discussion(mock_engine, mock_db_session):
    """Test a multi-round discussion."""
    mock_responses = [
        {
            "consensus": f"Round {i} consensus",
            "individual_responses": {
                "LLM1": f"Round {i} response 1",
                "LLM2": f"Round {i} response 2"
            }
        } for i in range(4)  # 4 rounds of discussion
    ]
    mock_engine.discuss = AsyncMock(side_effect=mock_responses)
    
    with patch('consensus_engine.engine.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.engine.ConsensusEngine', return_value=mock_engine):
        # Your test logic here
        pass