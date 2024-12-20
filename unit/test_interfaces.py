"""Tests for CLI and Web interfaces."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from consensus_engine.cli import main as cli_main
from rich.console import Console

console = Console()

@pytest.mark.asyncio
async def test_cli_discussion(cli_runner, mock_engine, mock_db_session):
    """Test CLI interface discussion."""
    test_prompt = "Test prompt"
    test_consensus = "Test consensus"

    # Create mock response
    mock_response = {
        "consensus": test_consensus,
        "individual_responses": {
            "TestLLM1": "Test response 1",
            "TestLLM2": "Test response 2"
        }
    }

    # Create a simple async mock function
    async def mock_discuss(prompt, callback=None):
        if callback:
            callback("Mock progress message")
        return mock_response

    # Set the mock discuss method
    mock_engine.discuss = mock_discuss

    with patch('consensus_engine.cli.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.cli.ConsensusEngine', return_value=mock_engine), \
         patch('builtins.input', return_value=test_prompt), \
         patch.dict('os.environ', {
             'OPENAI_API_KEY': 'test-key',
             'ANTHROPIC_API_KEY': 'test-key'
         }):
        result = cli_runner.invoke(cli_main, ['--cli'])
        print("CLI Output:", result.output)  # Debug print
        assert result.exit_code == 0
        assert test_prompt in result.output
        assert test_consensus in result.output 