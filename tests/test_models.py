"""Tests for LLM model implementations."""
import pytest
from unittest.mock import AsyncMock, patch
from consensus_engine.models.openai import OpenAILLM
from consensus_engine.models.anthropic import AnthropicLLM
from consensus_engine.config.settings import MODEL_CONFIGS

@pytest.fixture
def openai_llm():
    """Create an OpenAI LLM instance with mock API key."""
    return OpenAILLM("mock-api-key")

@pytest.fixture
def anthropic_llm():
    """Create an Anthropic LLM instance with mock API key."""
    return AnthropicLLM("mock-api-key")

@pytest.mark.asyncio
async def test_openai_response_format(openai_llm):
    """Test OpenAI response formatting."""
    mock_response = AsyncMock()
    mock_response.choices = [
        AsyncMock(
            message=AsyncMock(
                content="""
                UNDERSTANDING: Test understanding
                CONSTRAINTS: Test constraints
                INITIAL_POSITION: Test position
                CONFIDENCE: 0.8 Test confidence explanation
                """
            )
        )
    ]
    
    with patch('openai.AsyncOpenAI.chat.completions.create', return_value=mock_response):
        response = await openai_llm.generate_response("test prompt")
        assert isinstance(response, str)
        assert "UNDERSTANDING:" in response
        assert "CONFIDENCE:" in response

@pytest.mark.asyncio
async def test_anthropic_response_format(anthropic_llm):
    """Test Anthropic response formatting."""
    mock_response = AsyncMock()
    mock_response.content = [
        AsyncMock(
            text="""
            UNDERSTANDING: Test understanding
            CONSTRAINTS: Test constraints
            INITIAL_POSITION: Test position
            CONFIDENCE: 0.8 Test confidence explanation
            """
        )
    ]
    
    with patch('anthropic.AsyncAnthropic.messages.create', return_value=mock_response):
        response = await anthropic_llm.generate_response("test prompt")
        assert isinstance(response, str)
        assert "UNDERSTANDING:" in response
        assert "CONFIDENCE:" in response

@pytest.mark.asyncio
async def test_openai_error_handling(openai_llm):
    """Test OpenAI error handling."""
    with patch('openai.AsyncOpenAI.chat.completions.create', 
              side_effect=Exception("API Error")):
        with pytest.raises(Exception):
            await openai_llm.generate_response("test prompt")

@pytest.mark.asyncio
async def test_anthropic_error_handling(anthropic_llm):
    """Test Anthropic error handling."""
    with patch('anthropic.AsyncAnthropic.messages.create',
              side_effect=Exception("API Error")):
        with pytest.raises(Exception):
            await anthropic_llm.generate_response("test prompt")

def test_model_configuration():
    """Test model configuration loading."""
    openai_config = MODEL_CONFIGS["openai"]
    anthropic_config = MODEL_CONFIGS["anthropic"]
    
    assert "model" in openai_config
    assert "temperature" in openai_config
    assert "max_tokens" in openai_config
    assert "system_prompt" in openai_config
    
    assert "model" in anthropic_config
    assert "temperature" in anthropic_config
    assert "max_tokens" in anthropic_config
    assert "system_prompt" in anthropic_config

@pytest.mark.asyncio
async def test_openai_system_prompt(openai_llm):
    """Test OpenAI system prompt usage."""
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
    
    with patch('openai.AsyncOpenAI.chat.completions.create') as mock_create:
        await openai_llm.generate_response("test prompt")
        
        # Verify system prompt was included in the API call
        call_args = mock_create.call_args[1]
        messages = call_args['messages']
        assert any(m['role'] == 'system' for m in messages)

@pytest.mark.asyncio
async def test_anthropic_system_prompt(anthropic_llm):
    """Test Anthropic system prompt usage."""
    mock_response = AsyncMock()
    mock_response.content = [AsyncMock(text="Test response")]
    
    with patch('anthropic.AsyncAnthropic.messages.create') as mock_create:
        await anthropic_llm.generate_response("test prompt")
        
        # Verify system prompt was included in the API call
        call_args = mock_create.call_args[1]
        assert 'system' in call_args