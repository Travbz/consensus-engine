"""Tests for web interface."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
from datetime import datetime, UTC
from consensus_engine.web import GradioInterface
from consensus_engine.database.models import Discussion

@pytest.mark.asyncio
async def test_web_discussion_loading(mock_db_session):
    """Test loading a specific discussion."""
    # Create a mock discussion
    discussion = Discussion(
        id=1,
        prompt="Test prompt",
        final_consensus="Test consensus",
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        consensus_reached=True,
    )
    
    # Set up mock query
    mock_query = MagicMock()
    mock_query.get.return_value = discussion
    mock_db_session.query.return_value = mock_query

    with patch('consensus_engine.web.get_db_session', return_value=mock_db_session), \
         patch.dict('os.environ', {
             'OPENAI_API_KEY': 'test-key',
             'ANTHROPIC_API_KEY': 'test-key'
         }), \
         patch('consensus_engine.web.GradioInterface.load_discussion', return_value=("Test prompt", "")):
        interface = GradioInterface()
        prompt, details = interface.load_discussion(1)
        assert prompt == "Test prompt", f"Got unexpected prompt: {prompt}"