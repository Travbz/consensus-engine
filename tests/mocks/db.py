"""Mock database components for testing."""
from unittest.mock import MagicMock
from datetime import datetime, UTC
from typing import List, Dict, Any
from consensus_engine.database.models import Discussion, DiscussionRound, LLMResponse

class MockDiscussion:
    """Mock Discussion model that behaves like SQLAlchemy model."""
    def __init__(self, id: int = None, prompt: str = None, started_at: datetime = None, completed_at: datetime = None):
        self.id = id or 1
        self.prompt = prompt or "Test prompt"
        self.started_at = started_at or datetime.now(UTC)
        self.completed_at = completed_at or datetime.now(UTC)
        self.consensus_reached = False
        self.consensus = None
        self.rounds = []
        self._str_format = "{0.prompt} ({0.started_at:%Y-%m-%d})"
    
    def __str__(self):
        return self._str_format.format(self)

class MockRound:
    """Mock DiscussionRound model."""
    def __init__(self, discussion_id: int, round_number: int, responses: List[Dict[str, Any]] = None):
        self.discussion_id = discussion_id
        self.round_number = round_number
        self.round_type = ["PRE_FLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"][round_number]
        self.responses = [MockResponse(**r) for r in (responses or [])]
        self.similarity_score = 1.0
        self.timestamp = datetime.now(UTC)

class MockResponse:
    """Mock LLMResponse model."""
    def __init__(self, llm_name: str, response_text: str, confidence_score: float):
        self.llm_name = llm_name
        self.response_text = response_text
        self.confidence_score = confidence_score
        self.timestamp = datetime.now(UTC)

class MockQuery:
    """Mock query object that maintains state."""
    def __init__(self, session, model=None):
        self.session = session
        self.model = model
        self._filters = []
        self._order = None

    def filter(self, *args, **kwargs):
        """Add filters to query."""
        self._filters.extend(args)
        return self

    def order_by(self, *args):
        """Add order by clause."""
        self._order = args
        return self

    def desc(self):
        """Add descending order."""
        return self

    def all(self):
        """Return all results."""
        if self.model == Discussion:
            return self.session.discussions
        return []

    def first(self):
        """Return first result."""
        if self.model == Discussion and self.session.discussions:
            return self.session.discussions[0]
        return None

class MockDBSession:
    """Mock SQLAlchemy session that maintains state."""
    def __init__(self):
        self.discussions: List[MockDiscussion] = []
        self._add_sample_discussion()

    def _add_sample_discussion(self):
        """Add a sample discussion for testing."""
        discussion = MockDiscussion()
        discussion.consensus = "Test consensus"
        discussion.consensus_reached = True
        
        # Add a sample round
        round = MockRound(
            discussion_id=discussion.id,
            round_number=0,
            responses=[{
                "llm_name": "TestLLM",
                "response_text": "Test response",
                "confidence_score": 0.8
            }]
        )
        
        discussion.rounds.append(round)
        self.discussions.append(discussion)

    def query(self, model=None):
        """Start a query."""
        return MockQuery(self, model)

    def add(self, obj):
        """Add object to session."""
        if isinstance(obj, Discussion):
            # Convert to MockDiscussion
            mock_disc = MockDiscussion(
                id=len(self.discussions) + 1,
                prompt=obj.prompt,
                started_at=obj.started_at,
                completed_at=obj.completed_at
            )
            self.discussions.append(mock_disc)
            return mock_disc
        return obj

    def commit(self):
        """Commit the session."""
        pass

    def rollback(self):
        """Rollback the session."""
        pass

    def close(self):
        """Close the session."""
        pass