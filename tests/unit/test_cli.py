"""Tests for CLI interface."""
import pytest
import tempfile
import os
from unittest.mock import AsyncMock, patch, MagicMock
from consensus_engine.cli import main as cli_main, run_discussion
from consensus_engine.models.loader import ModelLoader
from click import Abort

def test_cli_discussion(cli_runner, mock_engine, mock_db_session, mock_model_loader):
    """Test running a discussion via CLI."""
    test_prompt = "Test prompt"
    test_consensus = "Test consensus"
    test_result = {
        "consensus": test_consensus,
        "individual_responses": {
            "TestLLM1": "Test response 1",
            "TestLLM2": "Test response 2",
            "TestLLM3": "Test response 3"
        }
    }

    async def mock_run(*args, **kwargs):
        return test_result

    env_vars = {
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key',
        'GOOGLE_API_KEY': 'test-key'
    }

    with patch('consensus_engine.cli.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.cli.ConsensusEngine', return_value=mock_engine), \
         patch('consensus_engine.cli.run_discussion', side_effect=mock_run), \
         patch.dict('os.environ', env_vars, clear=True), \
         patch('consensus_engine.models.loader.ModelLoader', return_value=mock_model_loader), \
         patch('consensus_engine.cli.ModelLoader.validate_models', return_value=True), \
         patch('consensus_engine.cli.ModelLoader.load_models', return_value=[MagicMock(), MagicMock(), MagicMock()]), \
         patch('consensus_engine.engine.ConsensusEngine.discuss', AsyncMock(return_value=test_result)):
        
        result = cli_runner.invoke(cli_main, ['--cli'], input=test_prompt + '\n')
        assert result.exit_code == 0, f"CLI failed with output: {result.output}"
        assert test_prompt in str(result.output)

def test_cli_missing_api_keys(cli_runner, mock_db_session, mock_model_loader):
    """Test CLI behavior with missing API keys."""
    mock_model_loader.load_models = MagicMock(return_value=[])
    mock_model_loader.validate_models = MagicMock(return_value=False)

    with patch('consensus_engine.cli.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.models.loader.ModelLoader', return_value=mock_model_loader), \
         patch.dict('os.environ', {}, clear=True):
        
        result = cli_runner.invoke(cli_main, ['--cli'], input='test prompt\n')
        assert result.exit_code == 1
        assert "Not enough valid models available" in str(result.output)

def test_cli_file_input(cli_runner, mock_engine, mock_db_session, mock_model_loader):
    """Test CLI with file input."""
    test_prompt = "Test prompt from file"
    test_consensus = "Test consensus"
    test_result = {
        "consensus": test_consensus,
        "individual_responses": {
            "TestLLM1": "Test response 1",
            "TestLLM2": "Test response 2",
            "TestLLM3": "Test response 3"
        }
    }

    env_vars = {
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key',
        'GOOGLE_API_KEY': 'test-key'
    }

    with cli_runner.isolated_filesystem():
        # Create test input file
        with open('test_input.txt', 'w') as f:
            f.write(test_prompt)
            f.flush()

        with patch('consensus_engine.cli.get_db_session', return_value=mock_db_session), \
             patch('consensus_engine.cli.ConsensusEngine', return_value=mock_engine), \
             patch('consensus_engine.cli.run_discussion', AsyncMock(return_value=test_result)), \
             patch.dict('os.environ', env_vars, clear=True), \
             patch('consensus_engine.models.loader.ModelLoader', return_value=mock_model_loader), \
             patch('consensus_engine.cli.ModelLoader.validate_models', return_value=True), \
             patch('consensus_engine.cli.ModelLoader.load_models', return_value=[MagicMock(), MagicMock(), MagicMock()]):

            result = cli_runner.invoke(cli_main, ['--cli', '--file', 'test_input.txt'])
            assert result.exit_code == 0, f"CLI failed with output: {result.output}"
            assert test_prompt in str(result.output)

def test_cli_model_loader(cli_runner, mock_db_session):
    """Test model loader integration in CLI."""
    test_prompt = "test prompt"
    test_result = {
        "consensus": "Test consensus",
        "individual_responses": {}
    }

    env_vars = {
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key',
        'GOOGLE_API_KEY': 'test-key'
    }

    # Create mock loader
    mock_loader = MagicMock()
    mock_engine = MagicMock()
    
    async def mock_discuss(*args, **kwargs):
        return test_result
    mock_engine.discuss = AsyncMock(side_effect=mock_discuss)

    with patch('consensus_engine.cli.get_db_session', return_value=mock_db_session), \
         patch.dict('os.environ', env_vars, clear=True), \
         patch('consensus_engine.models.loader.ModelLoader', return_value=mock_loader), \
         patch('consensus_engine.cli.ConsensusEngine', return_value=mock_engine), \
         patch('consensus_engine.cli.run_discussion', AsyncMock(side_effect=mock_discuss)):

        # Test insufficient models
        mock_loader.validate_models.return_value = False
        mock_loader.load_models.return_value = []
        result = cli_runner.invoke(cli_main, ['--cli'], input=test_prompt + '\n', catch_exceptions=False)
        assert result.exit_code == 1
        assert "Not enough valid models available" in result.output

        # Reset for successful case
        mock_loader.validate_models.return_value = True
        mock_loader.load_models.return_value = [MagicMock(), MagicMock(), MagicMock()]
        result = cli_runner.invoke(cli_main, ['--cli'], input=test_prompt + '\n')
        assert result.exit_code == 0

def test_cli_model_validation(cli_runner, mock_db_session):
    """Test model validation in CLI."""
    test_prompt = "test prompt"
    test_result = {
        "consensus": "Test consensus",
        "individual_responses": {}
    }

    env_vars = {
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key',
        'GOOGLE_API_KEY': 'test-key'
    }

    # Create mock loader and engine
    mock_loader = MagicMock()
    mock_engine = MagicMock()
    
    async def mock_discuss(*args, **kwargs):
        return test_result
    mock_engine.discuss = AsyncMock(side_effect=mock_discuss)

    with patch('consensus_engine.cli.get_db_session', return_value=mock_db_session), \
         patch.dict('os.environ', env_vars, clear=True), \
         patch('consensus_engine.models.loader.ModelLoader', return_value=mock_loader), \
         patch('consensus_engine.cli.ConsensusEngine', return_value=mock_engine), \
         patch('consensus_engine.cli.run_discussion', AsyncMock(side_effect=mock_discuss)):

        # Test failed validation
        mock_loader.validate_models.return_value = False
        mock_loader.load_models.return_value = []
        result = cli_runner.invoke(cli_main, ['--cli'], input=test_prompt + '\n', catch_exceptions=False)
        assert result.exit_code == 1
        assert "Not enough valid models available" in result.output

        # Reset for successful validation
        mock_loader.validate_models.return_value = True
        mock_loader.load_models.return_value = [MagicMock(), MagicMock(), MagicMock()]
        result = cli_runner.invoke(cli_main, ['--cli'], input=test_prompt + '\n')
        assert result.exit_code == 0

def test_cli_progress_display(cli_runner, mock_engine, mock_db_session, mock_model_loader):
    """Test progress display in CLI."""
    test_prompt = "Test prompt"
    test_result = {
        "consensus": "Test consensus",
        "individual_responses": {
            "TestLLM1": "Test response 1",
            "TestLLM2": "Test response 2",
            "TestLLM3": "Test response 3"
        }
    }

    # Create mock models that can be properly awaited
    mock_models = []
    for i in range(3):
        mock = AsyncMock()
        mock.name = f"TestLLM{i+1}"
        mock.generate.return_value = f"Test response {i+1}"
        mock_models.append(mock)

    # Create mock engine with async discuss method
    mock_engine.discuss = AsyncMock(return_value=test_result)

    env_vars = {
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key',
        'GOOGLE_API_KEY': 'test-key'
    }

    with patch('consensus_engine.cli.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.cli.ConsensusEngine', return_value=mock_engine), \
         patch.dict('os.environ', env_vars, clear=True), \
         patch('consensus_engine.models.loader.ModelLoader', return_value=mock_model_loader), \
         patch('consensus_engine.cli.ModelLoader.validate_models', return_value=True), \
         patch('consensus_engine.cli.ModelLoader.load_models', return_value=mock_models):

        result = cli_runner.invoke(cli_main, ['--cli'], input=test_prompt + '\n')
        assert result.exit_code == 0, f"CLI failed with output: {result.output}"