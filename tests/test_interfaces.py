"""Tests for CLI and web interfaces."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from click.testing import CliRunner
import tempfile
import os
from consensus_engine.cli import main as cli_main
from consensus_engine.web import GradioInterface

@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()

@pytest.fixture
def mock_engine():
    """Create a mock consensus engine."""
    mock = AsyncMock()
    mock.discuss = AsyncMock(return_value={
        "consensus": "Test consensus",
        "individual_responses": {
            "LLM1": "Test response 1",
            "LLM2": "Test response 2"
        }
    })
    return mock

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock = MagicMock()
    mock.query = MagicMock()
    return mock

def test_cli_basic_command(cli_runner):
    """Test basic CLI command execution."""
    with patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key'
    }):
        result = cli_runner.invoke(cli_main, ['--help'])
        assert result.exit_code == 0
        assert 'Consensus Engine' in result.output

def test_cli_list_discussions(cli_runner, mock_db_session):
    """Test listing discussions via CLI."""
    mock_discussions = [
        MagicMock(
            id=1,
            prompt="Test prompt 1",
            consensus_reached=1,
            started_at="2024-01-01"
        ),
        MagicMock(
            id=2,
            prompt="Test prompt 2",
            consensus_reached=0,
            started_at="2024-01-02"
        )
    ]
    
    with patch('consensus_engine.cli.get_db_session', return_value=mock_db_session):
        mock_db_session.query().all.return_value = mock_discussions
        result = cli_runner.invoke(cli_main, ['--list'])
        assert result.exit_code == 0
        assert "Test prompt 1" in result.output
        assert "Test prompt 2" in result.output

@pytest.mark.asyncio
async def test_cli_discussion(cli_runner, mock_engine, mock_db_session):
    """Test running a discussion via CLI."""
    with patch('consensus_engine.cli.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.cli.ConsensusEngine', return_value=mock_engine), \
         patch('asyncio.run') as mock_run, \
         patch.dict('os.environ', {
             'OPENAI_API_KEY': 'test-key',
             'ANTHROPIC_API_KEY': 'test-key'
         }):
        mock_run.return_value = {"consensus": "Test consensus"}
        result = cli_runner.invoke(cli_main, input="Test prompt\n")
        assert result.exit_code == 0
        assert "Test consensus" in result.output

@pytest.mark.asyncio
async def test_web_interface_creation():
    """Test web interface creation."""
    with patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key'
    }):
        interface = GradioInterface()
        assert interface is not None

@pytest.mark.asyncio
async def test_web_discussion_flow(mock_engine, mock_db_session):
    """Test discussion flow in web interface."""
    with patch('consensus_engine.web.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.web.ConsensusEngine', return_value=mock_engine), \
         patch.dict('os.environ', {
             'OPENAI_API_KEY': 'test-key',
             'ANTHROPIC_API_KEY': 'test-key'
         }):
        interface = GradioInterface()
        
        # Test discussion progress updates
        updates = []
        async for msg in interface._run_discussion("Test prompt"):
            updates.append(msg)
        
        assert any("Consensus Reached" in msg for msg in updates)

@pytest.mark.asyncio
async def test_web_interface_error_handling(mock_engine, mock_db_session):
    """Test web interface error handling."""
    mock_engine.discuss = AsyncMock(side_effect=Exception("Test error"))
    
    with patch('consensus_engine.web.get_db_session', return_value=mock_db_session), \
         patch('consensus_engine.web.ConsensusEngine', return_value=mock_engine):
        interface = GradioInterface()
        
        updates = []
        async for msg in interface._run_discussion("Test prompt"):
            updates.append(msg)
        
        assert any("Error" in msg for msg in updates)

def test_web_interface_port_handling():
    """Test web interface port selection."""
    with patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key'
    }), patch('gradio.Blocks.launch') as mock_launch:
        interface = GradioInterface()
        interface.launch(port=7860)
        
        mock_launch.assert_called_once()
        assert mock_launch.call_args[1]['server_port'] == 7860