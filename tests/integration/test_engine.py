"""Integration tests for the consensus engine."""
import pytest
import asyncio
from datetime import datetime, UTC
from consensus_engine.engine import ConsensusEngine
from consensus_engine.database.models import Discussion, DiscussionRound, LLMResponse
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_discussion_flow(mock_llms, mock_db_session):
    """Test a complete discussion flow."""
    # Override the calculate_similarity method to ensure consensus
    engine = ConsensusEngine(mock_llms, mock_db_session)
    engine._calculate_similarity = MagicMock(return_value=0.9)
    
    test_prompt = "Test prompt"
    
    messages = []
    async def mock_callback(msg: str):
        messages.append(msg)
        assert isinstance(msg, str)
        print(f"Progress: {msg}")
    
    # Reset mock session state
    mock_db_session.discussions = []
    
    result = await engine.discuss(test_prompt, mock_callback)
    
    print("\nFinal result:", result)  # Debug print
    
    # Check database state
    assert len(mock_db_session.discussions) > 0, "No discussions were recorded"
    
    saved_discussion = mock_db_session.discussions[0]
    assert saved_discussion.prompt == test_prompt
    assert saved_discussion.started_at is not None
    assert saved_discussion.completed_at is not None
    
    # Check results
    assert isinstance(result, dict)
    assert "consensus" in result, f"Expected 'consensus' in result keys: {result.keys()}"
    assert "individual_responses" in result
    assert all(llm.name in result["individual_responses"] for llm in mock_llms)
    
    # Check progress messages
    assert len(messages) > 0, "No progress messages were recorded"
    assert any("start" in msg.lower() for msg in messages), "Missing start message"
    assert any(f"Getting {mock_llms[0].name}'s response" in msg for msg in messages), "Missing LLM response message"