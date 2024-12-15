"""Validation utilities for consensus engine."""
from typing import Dict, Any, List
from ..database.models import RoundType

def validate_response_format(response: Dict[str, Any], round_type: RoundType) -> bool:
    """Validate response format for a given round."""
    required_fields = {
        RoundType.PRE_FLOP: ['UNDERSTANDING', 'CONSTRAINTS', 'INITIAL_POSITION', 'CONFIDENCE'],
        RoundType.FLOP: ['AGREEMENTS', 'DIFFERENCES', 'EVIDENCE', 'POSITION', 'CONFIDENCE'],
        RoundType.TURN: ['EVIDENCE_ANALYSIS', 'POSITION_UPDATE', 'COMPROMISE_AREAS', 'CONFIDENCE'],
        RoundType.RIVER: ['SYNTHESIS', 'RESOLUTION', 'REMAINING_ISSUES', 'CONFIDENCE'],
        RoundType.SHOWDOWN: ['FINAL_POSITION', 'IMPLEMENTATION', 'CONFIDENCE', 'DISSENTING_VIEWS']
    }
    
    return all(field in response for field in required_fields[round_type])

def validate_confidence_score(confidence: float) -> bool:
    """Validate confidence score."""
    return isinstance(confidence, (int, float)) and 0 <= confidence <= 1

def validate_round_sequence(sequence: List[RoundType]) -> bool:
    """Validate round sequence."""
    expected_sequence = [
        RoundType.PRE_FLOP,
        RoundType.FLOP,
        RoundType.TURN,
        RoundType.RIVER,
        RoundType.SHOWDOWN
    ]
    return sequence == expected_sequence
