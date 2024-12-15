"""Round management for consensus engine."""
from typing import Dict, Any, Optional
from ..database.models import RoundType, DiscussionRound
from ..protocols.base_protocol import BaseConsensusProtocol
import logging

logger = logging.getLogger(__name__)

class RoundManager:
    def __init__(self, protocol: BaseConsensusProtocol):
        self.protocol = protocol
        self.current_round = None
        self.round_history = []
        
    def start_round(self, round_type: RoundType) -> Dict[str, Any]:
        """Initialize a new round."""
        self.current_round = {
            'type': round_type,
            'responses': {},
            'metadata': {},
            'requirements': self.protocol.get_round_requirements(round_type)
        }
        return self.current_round
    
    def add_response(self, llm_name: str, response: Dict[str, Any]) -> None:
        """Add a response to the current round."""
        if not self.current_round:
            raise ValueError("No active round")
        self.current_round['responses'][llm_name] = response
        
    def can_proceed(self) -> bool:
        """Check if round can proceed to next stage."""
        if not self.current_round:
            return False
            
        next_rounds = self.protocol.get_round_sequence()
        current_idx = next_rounds.index(self.current_round['type'])
        
        if current_idx >= len(next_rounds) - 1:
            return False
            
        next_round = next_rounds[current_idx + 1]
        return self.protocol.validate_round_transition(
            self.current_round['type'],
            next_round,
            self.current_round
        )
    
    def complete_round(self) -> Dict[str, Any]:
        """Complete current round and prepare for next."""
        if not self.current_round:
            raise ValueError("No active round")
            
        round_data = self.current_round.copy()
        self.round_history.append(round_data)
        self.current_round = None
        return round_data
