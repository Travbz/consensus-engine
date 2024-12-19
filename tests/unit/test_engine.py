"""Tests for the consensus engine core functionality."""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from consensus_engine.engine import ConsensusEngine
from consensus_engine.config.round_config import ROUND_SEQUENCE
from ..conftest import MockLLM

@pytest.mark.asyncio
async def test_basic_consensus(mock_db_session):
    """Test basic consensus achievement."""
    llms = [
        MockLLM("MockLLM1", confidence=0.9),
        MockLLM("MockLLM2", confidence=0.9)
    ]
    engine = ConsensusEngine(llms, mock_db_session)
    
    messages = []
    async def progress_callback(msg: str):
        messages.append(msg)
        print("Progress:", msg)  # Debug print
    
    result = await engine.discuss("test_prompt", progress_callback)
    
    # Print all messages received
    print("\nAll messages received:")
    for msg in messages:
        print(msg)
    
    # Verify result structure
    assert isinstance(result, dict)
    
    # Verify either consensus or individual responses
    if "consensus" in result:
        assert isinstance(result["consensus"], str)
        assert "individual_responses" in result
        assert all(llm.name in result["individual_responses"] for llm in llms)
    else:
        assert all(llm.name in result for llm in llms)

@pytest.mark.asyncio
async def test_round_progression(mock_db_session):
    """Test that rounds progress correctly."""
    llms = [
        MockLLM("MockLLM1", confidence=0.9),
        MockLLM("MockLLM2", confidence=0.9)
    ]
    engine = ConsensusEngine(llms, mock_db_session)
    
    messages = []
    async def progress_callback(msg: str):
        messages.append(msg)
        print("Progress:", msg)  # Debug print
    
    await engine.discuss("test_prompt", progress_callback)
    
    # Print all messages for debugging
    print("\nAll messages received:")
    for msg in messages:
        print(msg)
    
    # Check each round type
    for round_type in ROUND_SEQUENCE:
        found = any(f"Starting {round_type}" in msg for msg in messages)
        assert found, f"Round {round_type} not found in messages"

@pytest.mark.asyncio
async def test_error_handling(mock_db_session):
    """Test error handling during discussion."""
    working_llm = MockLLM("WorkingLLM", confidence=0.9)
    failing_llm = MagicMock()
    failing_llm.name = "FailingLLM"
    failing_llm.generate_response = AsyncMock(side_effect=Exception("Test error"))
    
    engine = ConsensusEngine([working_llm, failing_llm], mock_db_session)
    
    messages = []
    async def progress_callback(msg: str):
        messages.append(msg)
        print("Progress:", msg)  # Debug print
    
    result = await engine.discuss("test_prompt", progress_callback)
    
    # Print all messages for debugging
    print("\nAll messages received:")
    for msg in messages:
        print(msg)
    
    # Check error was handled and working LLM continued
    assert isinstance(result, dict)
    assert any("error" in msg.lower() for msg in messages)
    assert any("FailingLLM" in msg and "error" in msg.lower() for msg in messages)
    
    # Verify working LLM's response is present
    if "consensus" in result:
        assert "individual_responses" in result
        assert "WorkingLLM" in result["individual_responses"]
        assert "FailingLLM" not in result["individual_responses"]
    else:
        assert "WorkingLLM" in result
        assert "FailingLLM" not in result

@pytest.mark.asyncio
async def test_consensus_threshold(mock_db_session):
    """Test consensus threshold behavior."""
    high_conf_llm = MockLLM("HighConfLLM", confidence=0.9)
    low_conf_llm = MockLLM("LowConfLLM", confidence=0.4)
    
    engine = ConsensusEngine([high_conf_llm, low_conf_llm], mock_db_session)
    
    messages = []
    async def progress_callback(msg: str):
        messages.append(msg)
        print("Progress:", msg)  # Debug print
    
    result = await engine.discuss("test_prompt", progress_callback)
    
    # Print all messages for debugging
    print("\nAll messages received:")
    for msg in messages:
        print(msg)
    
    # Verify either consensus or individual responses
    assert isinstance(result, dict)
    if "consensus" in result:
        assert "individual_responses" in result
        assert all(name in result["individual_responses"] for name in ["HighConfLLM", "LowConfLLM"])
    else:
        assert all(name in result for name in ["HighConfLLM", "LowConfLLM"])
    
    # Check confidence scores are mentioned in messages
    high_conf_found = any("0.9" in msg for msg in messages)
    low_conf_found = any("0.4" in msg for msg in messages)
    
    assert high_conf_found, "High confidence score (0.9) not found in messages"
    assert low_conf_found, "Low confidence score (0.4) not found in messages"