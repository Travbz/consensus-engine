"""Mock responses and data for testing."""
from datetime import datetime, UTC
from unittest.mock import MagicMock

def get_mock_llm_response(llm_name: str = "TestLLM", confidence: float = 0.8, round_num: int = 0) -> str:
    """Generate a standardized mock LLM response."""
    return f"""
UNDERSTANDING: Test understanding from {llm_name}
CONSTRAINTS: Test constraints
INITIAL_POSITION: Test position
CONFIDENCE: {confidence} Response from {llm_name} in round {round_num}
"""

def get_mock_openai_response() -> MagicMock:
    """Generate a mock OpenAI API response."""
    mock_message = MagicMock()
    mock_message.content = get_mock_llm_response("OpenAI")
    
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    
    return mock_response

def get_mock_anthropic_response() -> MagicMock:
    """Generate a mock Anthropic API response."""
    mock_content = MagicMock()
    mock_content.text = get_mock_llm_response("Anthropic")
    
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    
    return mock_response

def get_mock_progress_messages() -> list:
    """Generate mock progress messages."""
    return [
        "Starting consensus discussion...",
        "📍 Starting PRE_FLOP round...",
        "Getting LLM responses...",
        "📍 Starting FLOP round...",
        "Getting LLM responses...",
        "📍 Starting TURN round...",
        "Getting LLM responses...",
        "📍 Starting RIVER round...",
        "Getting LLM responses...",
        "📍 Starting SHOWDOWN round...",
        "Getting LLM responses...",
        "Consensus reached!"
    ]

def get_mock_discussion_data(
    prompt: str = "Test prompt",
    round_count: int = 5,
    llm_names: list = None
) -> dict:
    """Generate mock discussion data."""
    if llm_names is None:
        llm_names = ["TestLLM1", "TestLLM2"]
    
    rounds = []
    round_types = ["PRE_FLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"]
    
    for i in range(min(round_count, len(round_types))):
        responses = []
        for llm_name in llm_names:
            responses.append({
                "llm_name": llm_name,
                "response_text": get_mock_llm_response(llm_name, round_num=i),
                "confidence_score": 0.8
            })
        
        rounds.append({
            "round_number": i,
            "round_type": round_types[i],
            "responses": responses,
            "similarity_score": 1.0
        })
    
    return {
        "prompt": prompt,
        "consensus": "Test consensus",
        "consensus_reached": True,
        "started_at": datetime.now(UTC),
        "completed_at": datetime.now(UTC),
        "rounds": rounds
    }