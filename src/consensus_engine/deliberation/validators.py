"""Validation utilities for consensus engine."""
from typing import Dict, Any, List
from ..database.models import RoundType

def validate_response_format(response: Dict[str, Any], round_type: RoundType) -> bool:
    """Validate response format for a given round."""
    required_fields = {
        RoundType.PRE_FLOP: ['UNDERSTANDING', 'CONSTRAINTS', 'INITIAL_POSITION', 'CONFIDENCE'],
        RoundType.FLOP: ['FORMAT_PROPOSAL', 'INITIAL_SOLUTION', 'RATIONALE', 'CONFIDENCE'],
        RoundType.TURN: ['FORMAT_AGREEMENT', 'REFINED_SOLUTION', 'FORMAT_IMPROVEMENTS', 'CONFIDENCE'],
        RoundType.RIVER: ['IMPLEMENTATION', 'CONFIDENCE'],
        RoundType.SHOWDOWN: ['IMPLEMENTATION', 'CONFIDENCE']
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
