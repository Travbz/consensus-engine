"""Tests for LLM model implementations."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import google.generativeai as genai
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from consensus_engine.models.openai import OpenAILLM
from consensus_engine.models.anthropic import AnthropicLLM
from consensus_engine.models.gemini import GeminiLLM
from consensus_engine.config.settings import MODEL_CONFIGS, validate_environment, validate_model_config
from tests.mocks.clients import MockAsyncOpenAI, MockAsyncAnthropic, MockGemini
from tests.mocks.responses import (
    get_mock_llm_response,
    get_mock_openai_response,
    get_mock_anthropic_response,
    get_mock_gemini_response
)

@pytest.mark.asyncio
async def test_openai_response_format():
    """Test OpenAI response formatting."""
    llm = OpenAILLM("test-key")
    llm.client = MockAsyncOpenAI()
    
    response = await llm.generate_response("test prompt")
    assert isinstance(response, str)
    assert "UNDERSTANDING:" in response
    assert "CONFIDENCE:" in response

@pytest.mark.asyncio
async def test_anthropic_response_format():
    """Test Anthropic response formatting."""
    llm = AnthropicLLM("test-key")
    llm.client = MockAsyncAnthropic()
    
    response = await llm.generate_response("test prompt")
    assert isinstance(response, str)
    assert "UNDERSTANDING:" in response
    assert "CONFIDENCE:" in response

@pytest.mark.asyncio
async def test_gemini_response_format():
    """Test Gemini response formatting."""
    llm = GeminiLLM("test-key")
    llm.client = MockGemini()
    
    response = await llm.generate_response("test prompt")
    assert isinstance(response, str)
    assert "UNDERSTANDING:" in response
    assert "CONFIDENCE:" in response

@pytest.mark.asyncio
async def test_openai_error_handling():
    """Test OpenAI error handling."""
    mock_client = MockAsyncOpenAI()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
    
    llm = OpenAILLM("test-key")
    llm.client = mock_client
    
    with pytest.raises(Exception):
        await llm.generate_response("test prompt")

@pytest.mark.asyncio
async def test_anthropic_error_handling():
    """Test Anthropic error handling."""
    mock_client = MockAsyncAnthropic()
    mock_client.messages.create = AsyncMock(side_effect=Exception("API Error"))
    
    llm = AnthropicLLM("test-key")
    llm.client = mock_client
    
    with pytest.raises(Exception):
        await llm.generate_response("test prompt")

@pytest.mark.asyncio
async def test_gemini_error_handling():
    """Test Gemini error handling."""
    mock_client = MockGemini()
    mock_client.generate_content_async = AsyncMock(side_effect=Exception("API Error"))
    
    llm = GeminiLLM("test-key")
    llm.client = mock_client
    
    with pytest.raises(Exception):
        await llm.generate_response("test prompt")

@pytest.mark.asyncio
async def test_openai_system_prompt():
    """Test OpenAI system prompt usage."""
    mock_client = MockAsyncOpenAI()
    
    llm = OpenAILLM("test-key")
    llm.client = mock_client
    
    await llm.generate_response("test prompt")
    
    # Check if system message was included
    messages = mock_client.chat.completions.create.call_args[1]['messages']
    assert any(msg['role'] == 'system' for msg in messages)

@pytest.mark.asyncio
async def test_anthropic_system_prompt():
    """Test Anthropic system prompt usage."""
    mock_client = MockAsyncAnthropic()
    
    llm = AnthropicLLM("test-key")
    llm.client = mock_client
    
    await llm.generate_response("test prompt")
    
    # Check if system message was included
    call_args = mock_client.messages.create.call_args[1]
    assert 'system' in call_args

@pytest.mark.asyncio
async def test_gemini_system_prompt():
    """Test Gemini system prompt usage."""
    mock_client = MockGemini()
    
    llm = GeminiLLM("test-key")
    llm.client = mock_client
    
    await llm.generate_response("test prompt")
    
    # Verify the system prompt was included in the call
    call_args = mock_client.generate_content_async.call_args[0][0]
    assert llm.system_prompt in call_args

def test_model_config_validation():
    """Test model configuration validation."""
    # Test valid configs
    for model_name, config in MODEL_CONFIGS.items():
        assert validate_model_config(config), f"Invalid config for {model_name}"
    
    # Test invalid config
    invalid_config = {
        "enabled": True,
        "api_key_env": "TEST_KEY"
        # Missing required fields
    }
    assert not validate_model_config(invalid_config)

def test_environment_validation():
    """Test environment validation for models."""
    test_config = {
        "initialization": {
            "required_env_vars": ["TEST_API_KEY"],
            "required_packages": ["pytest"]
        }
    }
    
    # Test with missing env var
    assert not validate_environment(test_config)
    
    # Test with env var set
    with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
        assert validate_environment(test_config)

@pytest.mark.asyncio
async def test_model_configuration():
    """Test model configuration loading and application."""
    for model_name, config in MODEL_CONFIGS.items():
        if model_name == "openai":
            llm = OpenAILLM("test-key")
            assert llm.model == config["model"]
            assert llm.temperature == config["temperature"]
            assert llm.max_tokens == config["max_tokens"]
        elif model_name == "anthropic":
            llm = AnthropicLLM("test-key")
            assert llm.model == config["model"]
            assert llm.temperature == config["temperature"]
            assert llm.max_tokens == config["max_tokens"]
        elif model_name == "gemini":
            llm = GeminiLLM("test-key")
            assert llm.model == config["model"]
            assert llm.temperature == config["temperature"]
            assert llm.max_tokens == config["max_tokens"]

def test_model_name_property():
    """Test model name property."""
    openai_llm = OpenAILLM("test-key")
    anthropic_llm = AnthropicLLM("test-key")
    gemini_llm = GeminiLLM("test-key")
    
    assert openai_llm.name == "OpenAI"
    assert anthropic_llm.name == "Anthropic"
    assert gemini_llm.name == "Gemini"