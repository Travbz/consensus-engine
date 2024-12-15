"""Round configuration for the Consensus Engine."""

ROUND_CONFIGS = {
    "PRE_FLOP": {
        "name": "Initial Setup",
        "required_confidence": 0.0,
        "max_duration": 300,  # seconds
        "requirements": {
            "min_participants": 2,
            "evidence_required": False
        }
    },
    "FLOP": {
        "name": "Opening Statements",
        "required_confidence": 0.5,
        "max_duration": 600,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        }
    },
    "TURN": {
        "name": "Evidence Review",
        "required_confidence": 0.6,
        "max_duration": 600,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        }
    },
    "RIVER": {
        "name": "Reconciliation",
        "required_confidence": 0.7,
        "max_duration": 600,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        }
    },
    "SHOWDOWN": {
        "name": "Resolution",
        "required_confidence": 0.75,
        "max_duration": 300,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        }
    }
}

ROUND_PROMPTS = {
    "PRE_FLOP": """
    You are entering the initial setup phase of a consensus discussion.
    Focus on:
    1. Understanding the core question/problem
    2. Identifying key constraints and requirements
    3. Establishing your initial position
    
    Format your response as:
    UNDERSTANDING: [Your interpretation of the question]
    CONSTRAINTS: [Key limitations/requirements identified]
    INITIAL_POSITION: [Your preliminary stance]
    CONFIDENCE: [0.0-1.0 with brief justification]
    """,
    
    "FLOP": """
    Review the initial positions of all participants.
    Focus on:
    1. Areas of agreement
    2. Key differences
    3. Supporting evidence for your position
    
    Format your response as:
    AGREEMENTS: [Points of consensus]
    DIFFERENCES: [Areas of disagreement]
    EVIDENCE: [Supporting information]
    POSITION: [Your current stance]
    CONFIDENCE: [0.0-1.0 with brief justification]
    """,
    
    "TURN": """
    Analyze the evidence presented by all participants.
    Focus on:
    1. Evidence evaluation
    2. Position refinement
    3. Areas for compromise
    
    Format your response as:
    EVIDENCE_ANALYSIS: [Evaluation of all presented evidence]
    POSITION_UPDATE: [Your refined stance]
    COMPROMISE_AREAS: [Potential areas for agreement]
    CONFIDENCE: [0.0-1.0 with brief justification]
    """,
    
    "RIVER": """
    Work towards final consensus.
    Focus on:
    1. Synthesizing positions
    2. Resolving remaining differences
    3. Building unified response
    
    Format your response as:
    SYNTHESIS: [Combined understanding]
    RESOLUTION: [Proposed unified position]
    REMAINING_ISSUES: [Any unresolved points]
    CONFIDENCE: [0.0-1.0 with brief justification]
    """,
    
    "SHOWDOWN": """
    Finalize consensus position.
    Focus on:
    1. Final position statement
    2. Confidence assessment
    3. Implementation considerations
    
    Format your response as:
    FINAL_POSITION: [Concrete consensus statement]
    IMPLEMENTATION: [How to apply this consensus]
    CONFIDENCE: [0.0-1.0 with brief justification]
    DISSENTING_VIEWS: [Any remaining disagreements]
    """
}

ROUND_SEQUENCE = ["PRE_FLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"]