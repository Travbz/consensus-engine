"""Mock database objects for testing."""
from unittest.mock import MagicMock
from consensus_engine.database.models import Discussion, DiscussionRound, LLMResponse

class MockDBSession:
    """Mock database session for testing."""
    def __init__(self):
        self.discussions = []
        self.rounds = []
        self.responses = []
    
    def add(self, obj):
        """Mock add method."""
        if isinstance(obj, Discussion):
            self.discussions.append(obj)
        elif isinstance(obj, DiscussionRound):
            self.rounds.append(obj)
        elif isinstance(obj, LLMResponse):
            self.responses.append(obj)
    
    def commit(self):
        """Mock commit method."""
        pass
    
    def close(self):
        """Mock close method."""
        pass
    
    def query(self, model):
        """Mock query method."""
        if model == Discussion:
            return MagicMock(
                all=lambda: self.discussions,
                get=lambda id: next((d for d in self.discussions if d.id == id), None)
            )
        return MagicMock()