"""Tests for CLI interface."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from consensus_engine.cli import main as cli_main, run_discussion

def test_cli_discussion(cli_runner, mock_engine, mock_db_session):
    """Test running a discussion via CLI."""
    test_prompt = "Test prompt"
    test_consensus = "Test consensus"
    test_result = {
        "consensus": test_consensus,
        "individual_responses": {
            "TestLLM1": "Test response 1",
            "TestLLM2": "Test response 2"
        }
    }

    # Create simple sync mock
    async def mock_run(*args, **kwargs):
        return test_result

    with patch('consensus_engine.cli.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.cli.ConsensusEngine', return_value=mock_engine), \
         patch('builtins.input', return_value=test_prompt), \
         patch('consensus_engine.cli.run_discussion', mock_run), \
         patch.dict('os.environ', {
             'OPENAI_API_KEY': 'test-key',
             'ANTHROPIC_API_KEY': 'test-key'
         }):
        result = cli_runner.invoke(cli_main, ['--cli'])
        assert result.exit_code == 0
        assert test_prompt in result.output

def test_cli_error_handling(cli_runner, mock_engine, mock_db_session):
    """Test CLI error handling."""
    test_prompt = "Test prompt"
    test_error = "Test error"

    # Create simple sync mock that raises error
    def mock_run(*args, **kwargs):
        raise Exception(test_error)

    with patch('consensus_engine.cli.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.cli.ConsensusEngine', return_value=mock_engine), \
         patch('builtins.input', return_value=test_prompt), \
         patch('consensus_engine.cli.run_discussion', side_effect=Exception(test_error)), \
         patch.dict('os.environ', {
             'OPENAI_API_KEY': 'test-key',
             'ANTHROPIC_API_KEY': 'test-key'
         }):
        result = cli_runner.invoke(cli_main, ['--cli'])
        print(f"Output: {result.output}")
        print(f"Exit code: {result.exit_code}")
        assert result.exit_code == 1
        assert test_error in str(result.output)

def test_cli_file_input(cli_runner, mock_engine, mock_db_session):
    """Test CLI with file input."""
    test_prompt = "Test prompt from file"
    test_consensus = "Test consensus"
    test_result = {
        "consensus": test_consensus,
        "individual_responses": {
            "TestLLM1": "Test response 1",
            "TestLLM2": "Test response 2"
        }
    }

    # Create simple sync mock
    async def mock_run(*args, **kwargs):
        return test_result

    with cli_runner.isolated_filesystem(), \
         patch('consensus_engine.cli.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.cli.ConsensusEngine', return_value=mock_engine), \
         patch('consensus_engine.cli.run_discussion', mock_run), \
         patch.dict('os.environ', {
             'OPENAI_API_KEY': 'test-key',
             'ANTHROPIC_API_KEY': 'test-key'
         }):
        # Create test input file
        with open('test_input.txt', 'w') as f:
            f.write(test_prompt)

        result = cli_runner.invoke(cli_main, ['--cli', '--file', 'test_input.txt'])
        assert result.exit_code == 0, f"Got exit code {result.exit_code}, expected 0"
        assert test_prompt in result.output