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
    
    "FLOP" : """
    1. First, review others' initial responses and propose a solution format:

    FORMAT_PROPOSAL:
    [Propose 2-3 key sections that any solution should include]
    [Explain why these sections are important]

    INITIAL_SOLUTION:
    [Present your initial solution using your proposed format]

    RATIONALE:
    [Explain why your format would work well for this problem]

    CONFIDENCE: [0.0-1.0 with explanation]
    """,
    
    "TURN": """
    Review the format proposals from the FLOP round.

    FORMAT_AGREEMENT:
    [State which parts of proposed formats you agree with]
    [Suggest specific refinements needed]

    REFINED_SOLUTION:
    [Present your solution using the most commonly agreed sections]
    [Adapt your previous response to match common structure]

    FORMAT_IMPROVEMENTS:
    [Suggest any final format adjustments needed]

    CONFIDENCE: [0.0-1.0 with explanation]
    """,
    
    "RIVER": """
    Based on previous format discussions, we will use this structure:
    IMPLEMENTATION: {agreed_format}

    Present your solution using EXACTLY this format, no additions or modifications.
    Include ONLY the sections listed above.

    If you have concerns about the format, you must still use it exactly as specified.
    You can note format concerns in your confidence score explanation.

    Lock in on the agreed format and solution, do not deviate at all

    CONFIDENCE: [0.0-1.0 with explanation of both solution and format confidence]
    """,
    
    "SHOWDOWN": """
    Using the agreed format, provide ONLY the solution to the original prompt:
    IMPLEMENTATION: {strict_format}

    No meta-discussion, no explanations.
    Focus only on answering the original question using our agreed structure.
    CONFIDENCE: [0.0-1.0 with explanation of both solution and format confidence]
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