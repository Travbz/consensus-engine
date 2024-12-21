"""Tests for web interface."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC
from sqlalchemy import or_
from consensus_engine.web import GradioInterface
from consensus_engine.database.models import Discussion

def test_web_discussion_loading(mock_db_session):
    """Test loading a specific discussion."""
    # Create a mock discussion
    test_discussion = Discussion(
        id=1,
        prompt="Test prompt",
        final_consensus="Test consensus",
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        consensus_reached=True,
        rounds=[]  # Add empty rounds list
    )
    
    # Create a proper mock query chain
    class MockQuery:
        def __init__(self):
            self.test_discussion = test_discussion
            
        def filter(self, *args, **kwargs):
            return self
            
        def first(self):
            return self.test_discussion
            
        def all(self):
            return [self.test_discussion]

    # Set up the mock session
    mock_db_session.query = MagicMock(return_value=MockQuery())

    # Mock environment variables
    env_vars = {
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key',
        'GOOGLE_API_KEY': 'test-key'
    }

    with patch('consensus_engine.web.get_db_session', return_value=mock_db_session), \
         patch.dict('os.environ', env_vars, clear=True):
        
        interface = GradioInterface()
        prompt, details = interface.load_discussion(1)
        
        assert prompt == "Test prompt", f"Expected 'Test prompt', got {prompt}"
        assert "Test consensus" in details, f"Expected 'Test consensus' in {details}"
        assert mock_db_session.query.called, "Database query was not called"