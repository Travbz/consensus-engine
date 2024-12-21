"""Mock responses for testing."""
from unittest.mock import MagicMock

def get_mock_llm_response():
    """Get a standard mock LLM response."""
    return """UNDERSTANDING: Test understanding
APPROACH: Test approach
SOLUTION: Test solution
CONFIDENCE: 95
"""

def get_mock_openai_response():
    """Get a mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = get_mock_llm_response()
    return mock_response

def get_mock_anthropic_response():
    """Get a mock Anthropic API response."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = get_mock_llm_response()
    return mock_response

def get_mock_gemini_response():
    """Get a mock Gemini API response."""
    mock_response = MagicMock()
    mock_response.text = get_mock_llm_response()
    return mock_response

def get_mock_progress_messages():
    """Get a list of mock progress messages."""
    return [
        "Starting discussion...",
        "Getting response from Model 1...",
        "Model 1 responded with confidence: 0.8",
        "Getting response from Model 2...",
        "Model 2 responded with confidence: 0.9",
        "Round 1 Summary:",
        "Similarity Score: 0.85",
        "Average Confidence: 0.85"
    ]