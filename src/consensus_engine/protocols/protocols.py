# src/consensus_engine/protocols/base_protocol.py

"""Base protocol for consensus building."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ..database.models import RoundType

class BaseConsensusProtocol(ABC):
    @abstractmethod
    def get_round_sequence(self) -> List[RoundType]:
        """Return the sequence of rounds for this protocol."""
        pass
    
    @abstractmethod
    def get_round_requirements(self, round_type: RoundType) -> Dict[str, Any]:
        """Get requirements for a specific round."""
        pass
    
    @abstractmethod
    def validate_round_transition(self, 
                                current_round: RoundType,
                                next_round: RoundType,
                                round_data: Dict[str, Any]) -> bool:
        """Validate if transition to next round is allowed."""
        pass
    
    @abstractmethod
    def check_consensus(self,
                       round_type: RoundType,
                       responses: Dict[str, str],
                       metadata: Dict[str, Any]) -> bool:
        """Check if consensus has been reached for the current round."""
        pass

# src/consensus_engine/protocols/poker_protocol.py

"""Poker-style consensus protocol implementation."""
from typing import Dict, Any, List
from .base_protocol import BaseConsensusProtocol
from ..database.models import RoundType
from ..config.round_config import ROUND_CONFIGS

class PokerConsensusProtocol(BaseConsensusProtocol):
    def get_round_sequence(self) -> List[RoundType]:
        return [RoundType.PRE_FLOP, RoundType.FLOP, RoundType.TURN, 
                RoundType.RIVER, RoundType.SHOWDOWN]
    
    def get_round_requirements(self, round_type: RoundType) -> Dict[str, Any]:
        return ROUND_CONFIGS[round_type.value]["requirements"]
    
    def validate_round_transition(self,
                                current_round: RoundType,
                                next_round: RoundType,
                                round_data: Dict[str, Any]) -> bool:
        # Get confidence scores from round data
        confidence_scores = [response.get('confidence_score', 0)
                           for response in round_data.get('responses', [])]
        
        if not confidence_scores:
            return False
            
        # Calculate average confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Get required confidence for next round
        required_confidence = ROUND_CONFIGS[next_round.value]["required_confidence"]
        
        # Validate transition
        return (avg_confidence >= required_confidence and
                self._validate_round_requirements(round_data, current_round))
    
    def _validate_round_requirements(self,
                                   round_data: Dict[str, Any],
                                   round_type: RoundType) -> bool:
        requirements = self.get_round_requirements(round_type)
        
        # Check minimum participants
        if len(round_data.get('responses', [])) < requirements['min_participants']:
            return False
            
        # Check evidence requirements
        if (requirements['evidence_required'] and
            not all('evidence' in r.get('response_metadata', {})
                   for r in round_data.get('responses', []))):
            return False
            
        # Check verification requirements
        if (requirements['verification_required'] and
            not all('verification' in r.get('response_metadata', {})
                   for r in round_data.get('responses', []))):
            return False
            
        return True
    
    def check_consensus(self,
                       round_type: RoundType,
                       responses: Dict[str, str],
                       metadata: Dict[str, Any]) -> bool:
        required_confidence = ROUND_CONFIGS[round_type.value]["required_confidence"]
        
        if round_type == RoundType.SHOWDOWN:
            # For final round, check if all participants agree on final position
            final_positions = [m.get('final_position') 
                             for m in metadata.get('response_metadata', [])]
            return len(set(final_positions)) == 1
        else:
            # For other rounds, check confidence scores
            confidence_scores = [m.get('confidence_score', 0) 
                               for m in metadata.get('response_metadata', [])]
            return (sum(confidence_scores) / len(confidence_scores) >= 
                   required_confidence)