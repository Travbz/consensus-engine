"""Round configuration for the Consensus Engine."""

CONFIDENCE_GUIDANCE = """
Confidence Guidelines (0.0-1.0):
- Base your confidence on agreement with other participants
- Consider how close your position is to others
- Account for shared evidence and reasoning
- Confidence should reflect likelihood of consensus

Current consensus metrics:
- Text similarity between responses
- Code similarity (for programming solutions)
- Shared evidence and citations 
- Common terminology and framing

Your confidence score impacts consensus:
- Higher scores (>0.8) require strong alignment with others
- Medium scores (0.5-0.7) show potential for consensus
- Lower scores (<0.5) indicate significant differences
"""

ROUND_CONFIGS = {
    "PRE_FLOP": {
        "name": "Initial Understanding",
        "required_confidence": 0.0,
        "max_duration": 300,
        "requirements": {
            "min_participants": 2,
            "evidence_required": False
        },
        "consensus_guidance": """
        In this round:
        1. Focus on shared understanding and terminology
        2. Note areas of agreement and disagreement
        3. Current similarity score: {similarity}
        4. Average confidence: {avg_confidence}
        5. Consensus requires {consensus_threshold} similarity
        
        To increase consensus likelihood:
        - Use consistent terminology
        - Frame the problem similarly to others
        - Build on shared understanding
        """
    },
    "FLOP": {
        "name": "Opening Analysis",
        "required_confidence": 0.5,
        "max_duration": 600,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        },
        "consensus_guidance": """
        Progress metrics:
        1. Current similarity: {similarity}
        2. Required similarity: {consensus_threshold}
        3. Group confidence: {avg_confidence}
        4. Main differences: {key_differences}
        
        To align positions:
        - Reference shared evidence
        - Address key differences
        - Use similar structure and terminology
        """
    },
    "TURN": {
        "name": "Position Refinement",
        "required_confidence": 0.6,
        "max_duration": 600,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        },
        "consensus_guidance": """
        Current metrics:
        1. Similarity score: {similarity}
        2. Consensus target: {consensus_threshold}
        3. Response alignment: {alignment_areas}
        4. Outstanding issues: {remaining_issues}
        
        Focus areas:
        - Resolve remaining differences
        - Strengthen shared positions
        - Match successful patterns
        """
    },
    "RIVER": {
        "name": "Consensus Building",
        "required_confidence": 0.7,
        "max_duration": 600,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        },
        "consensus_guidance": """
        Consensus status:
        1. Current similarity: {similarity}
        2. Target threshold: {consensus_threshold}
        3. Group confidence: {avg_confidence}
        4. Key alignments: {key_alignments}
        
        For code solutions:
        - Match structure and patterns
        - Use consistent variable names
        - Follow same error handling
        - Aim for identical output format
        """
    },
    "SHOWDOWN": {
        "name": "Final Resolution",
        "required_confidence": 0.75,
        "max_duration": 300,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        },
        "consensus_guidance": """
        Final metrics:
        1. Current similarity: {similarity}
        2. Required for consensus: {consensus_threshold}
        3. Collective confidence: {avg_confidence}
        
        For consensus approval:
        - Responses must be {consensus_threshold} similar
        - Code solutions must be functionally identical
        - Using same terminology and structure
        - Sharing core evidence and reasoning
        """
    }
}

RESPONSE_FORMAT = {
    "PRE_FLOP": """
    Format your response:
    UNDERSTANDING: [Problem interpretation]
    CONSTRAINTS: [Key limitations]
    INITIAL_POSITION: [Starting stance]
    CONFIDENCE: [0.0-1.0 score + why]
    """,
    
    "FLOP": """
    Format your response:
    SHARED_GROUND: [Common understanding]
    DIFFERENCES: [Areas to resolve]
    EVIDENCE: [Supporting information]
    UPDATED_POSITION: [Current stance]
    CONFIDENCE: [0.0-1.0 score + justification]
    """,
    
    "TURN": """
    Format your response:
    PROGRESS: [Consensus development]
    ALIGNMENTS: [Agreement areas]
    RESOLUTION: [Difference handling]
    POSITION: [Updated stance]
    CONFIDENCE: [0.0-1.0 score + reasoning]
    """,
    
    "RIVER": """
    Format your response:
    SYNTHESIS: [Combined position]
    IMPLEMENTATION: [Solution details]
    REMAINING_ISSUES: [Final concerns]
    CONFIDENCE: [0.0-1.0 score + rationale]
    """,
    
    "SHOWDOWN": """
    Format your response:
    IMPLEMENTATION: [Full details/code]
    """
}

# Sequence preservation
ROUND_SEQUENCE = ["PRE_FLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"]

# Code-specific guidance
CODE_CONSENSUS_GUIDANCE = """
For code solutions:
1. Match structure and organization
2. Use identical:
   - Variable names
   - Function signatures
   - Error handling
   - Comment style
3. Produce same output format
4. Follow same patterns
"""

for config in ROUND_CONFIGS.values():
    if "consensus_guidance" in config:
        config["consensus_guidance"] = config["consensus_guidance"].strip()

__all__ = ['ROUND_CONFIGS', 'RESPONSE_FORMAT', 'ROUND_SEQUENCE', 'CONFIDENCE_GUIDANCE', 'CODE_CONSENSUS_GUIDANCE']