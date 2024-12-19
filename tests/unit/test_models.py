"""Tests for LLM model implementations."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from consensus_engine.models.openai import OpenAILLM
from consensus_engine.models.anthropic import AnthropicLLM
from consensus_engine.config.settings import MODEL_CONFIGS
from tests.mocks.clients import MockAsyncOpenAI, MockAsyncAnthropic
from tests.mocks.responses import (
    get_mock_llm_response,
    get_mock_openai_response,
    get_mock_anthropic_response
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