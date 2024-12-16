"""Tests for the consensus engine core functionality."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from consensus_engine.engine import ConsensusEngine
from consensus_engine.models.base import BaseLLM

@pytest.fixture
def mock_llm():
    """Create a mock language model."""
    mock = AsyncMock(spec=BaseLLM)
    mock.generate = AsyncMock(return_value="Test response")
    return mock

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock = MagicMock()
    mock.add = MagicMock()
    mock.commit = MagicMock()
    return mock

@pytest.mark.asyncio
async def test_engine_initialization():
    """Test engine initialization."""
    with patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key'
    }):
        engine = ConsensusEngine()
        assert engine is not None

@pytest.mark.asyncio
async def test_engine_discussion(mock_llm, mock_db_session):
    """Test running a discussion."""
    with patch('consensus_engine.engine.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.engine.load_model', return_value=mock_llm):
        engine = ConsensusEngine()
        result = await engine.discuss("Test prompt")
        
        assert "consensus" in result
        assert "individual_responses" in result
        mock_llm.generate.assert_called()

@pytest.mark.asyncio
async def test_engine_multiple_rounds(mock_llm, mock_db_session):
    """Test running multiple discussion rounds."""
    with patch('consensus_engine.engine.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.engine.load_model', return_value=mock_llm):
        engine = ConsensusEngine()
        result = await engine.discuss("Test prompt", rounds=3)
        
        assert mock_llm.generate.call_count >= 3
        assert "consensus" in result

@pytest.mark.asyncio
async def test_engine_model_selection(mock_llm, mock_db_session):
    """Test model selection."""
    with patch('consensus_engine.engine.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.engine.load_model', return_value=mock_llm):
        engine = ConsensusEngine()
        result = await engine.discuss("Test prompt", models=["gpt-4", "claude-2"])
        
        assert mock_llm.generate.called
        assert "individual_responses" in result

@pytest.mark.asyncio
async def test_engine_error_handling(mock_llm, mock_db_session):
    """Test error handling during discussion."""
    mock_llm.generate = AsyncMock(side_effect=Exception("Test error"))
    
    with patch('consensus_engine.engine.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.engine.load_model', return_value=mock_llm):
        engine = ConsensusEngine()
        
        with pytest.raises(Exception):
            await engine.discuss("Test prompt")

@pytest.mark.asyncio
async def test_engine_database_integration(mock_llm, mock_db_session):
    """Test database integration."""
    with patch('consensus_engine.engine.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.engine.load_model', return_value=mock_llm):
        engine = ConsensusEngine()
        await engine.discuss("Test prompt")
        
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()