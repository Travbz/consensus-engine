"""Integration tests for the consensus engine."""
import pytest
import asyncio
from datetime import datetime, UTC
from consensus_engine.engine import ConsensusEngine
from consensus_engine.database.models import Discussion
from unittest.mock import AsyncMock, patch, MagicMock
from tests.mocks.responses import get_mock_llm_response, get_mock_progress_messages
from tests.fixtures.conftest import MockLLM  # Added this import

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_discussion_flow(mock_llms, mock_db_session):
    """Test a complete discussion flow."""
    engine = ConsensusEngine(mock_llms, mock_db_session)
    test_prompt = "Test prompt"
    
    async def mock_callback(msg: str):
        assert isinstance(msg, str)
        await asyncio.sleep(0)
    
    # Reset mock session state
    mock_db_session.discussions = []
    
    result = await engine.discuss(test_prompt, mock_callback)
    
    # Check database state
    assert len(mock_db_session.discussions) > 0
    discussion = mock_db_session.discussions[0]
    assert discussion.prompt == test_prompt
    assert discussion.completed_at is not None
    
    # Check results
    assert isinstance(result, dict)
    assert "consensus" in result
    assert "individual_responses" in result
    for llm in mock_llms:
        assert llm.name in result["individual_responses"]