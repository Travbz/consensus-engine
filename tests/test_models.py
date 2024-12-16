"""Tests for language model implementations."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from consensus_engine.models.openai import OpenAILLM
from consensus_engine.models.anthropic import AnthropicLLM
from consensus_engine.models.loader import ModelLoader

@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client."""
    mock = AsyncMock()
    mock.chat.completions.create = AsyncMock(return_value=MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test OpenAI response"))]
    ))
    return mock

@pytest.fixture
def mock_anthropic():
    """Create a mock Anthropic client."""
    mock = AsyncMock()
    mock.messages.create = AsyncMock(return_value=MagicMock(
        content=[MagicMock(text="Test Anthropic response")]
    ))
    return mock

@pytest.mark.asyncio
async def test_openai_model():
    """Test OpenAI model generation."""
    with patch('openai.AsyncClient', return_value=AsyncMock()) as mock_client:
        model = OpenAILLM("test-key", "gpt-4")
        response = await model.generate_response("Test prompt")
        assert isinstance(response, str)
        mock_client.return_value.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_anthropic_model():
    """Test Anthropic model generation."""
    with patch('anthropic.AsyncAnthropic', return_value=AsyncMock()) as mock_client:
        model = AnthropicLLM("test-key", "claude-2")
        response = await model.generate_response("Test prompt")
        assert isinstance(response, str)
        mock_client.return_value.messages.create.assert_called_once()

@pytest.mark.asyncio
async def test_openai_error_handling():
    """Test OpenAI error handling."""
    with patch('openai.AsyncClient', return_value=AsyncMock()) as mock_client:
        mock_client.return_value.chat.completions.create.side_effect = Exception("API Error")
        model = OpenAILLM("test-key", "gpt-4")
        with pytest.raises(Exception):
            await model.generate_response("Test prompt")

@pytest.mark.asyncio
async def test_anthropic_error_handling():
    """Test Anthropic error handling."""
    with patch('anthropic.AsyncAnthropic', return_value=AsyncMock()) as mock_client:
        mock_client.return_value.messages.create.side_effect = Exception("API Error")
        model = AnthropicLLM("test-key", "claude-2")
        with pytest.raises(Exception):
            await model.generate_response("Test prompt")

def test_model_loader():
    """Test model loading functionality."""
    with patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key'
    }), patch('consensus_engine.models.loader.get_enabled_models', return_value={
        'gpt-4': {
            'module_path': 'consensus_engine.models.openai',
            'class_name': 'OpenAILLM',
            'model': 'gpt-4',
            'temperature': 0.7,
            'max_tokens': 2000,
            'system_prompt': 'test prompt'
        },
        'claude-2': {
            'module_path': 'consensus_engine.models.anthropic',
            'class_name': 'AnthropicLLM',
            'model': 'claude-2',
            'temperature': 0.7,
            'max_tokens': 2000,
            'system_prompt': 'test prompt'
        }
    }):
        models = ModelLoader.load_models()
        assert len(models) == 2
        assert isinstance(models[0], OpenAILLM)
        assert isinstance(models[1], AnthropicLLM)

def test_model_loader_validation():
    """Test model loader validation."""
    with patch('consensus_engine.models.loader.CONSENSUS_SETTINGS', {
        'min_models': 2,
        'max_models': 3
    }):
        models = [MagicMock(spec=OpenAILLM), MagicMock(spec=AnthropicLLM)]
        assert ModelLoader.validate_models(models) is True

@pytest.mark.asyncio
async def test_openai_response_parsing(mock_openai):
    """Test OpenAI response parsing."""
    with patch('openai.AsyncClient', return_value=mock_openai):
        model = OpenAILLM("test-key", "gpt-4")
        response = await model.generate_response("Test prompt")
        assert "Test OpenAI response" in response

@pytest.mark.asyncio
async def test_anthropic_response_parsing(mock_anthropic):
    """Test Anthropic response parsing."""
    with patch('anthropic.AsyncAnthropic', return_value=mock_anthropic):
        model = AnthropicLLM("test-key", "claude-2")
        response = await model.generate_response("Test prompt")
        assert "Test Anthropic response" in response