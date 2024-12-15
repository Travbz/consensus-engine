"""Round configuration for the Consensus Engine."""

ROUND_CONFIGS = {
    "PRE_FLOP": {
        "name": "Initial Understanding",
        "required_confidence": 0.0,
        "max_duration": 300,  # seconds
        "requirements": {
            "min_participants": 2,
            "evidence_required": False
        },
        "consensus_guidance": "Focus on establishing common ground in understanding the question. " +
                            "Use similar terminology where possible and aim to match confidence levels realistically."
    },
    "FLOP": {
        "name": "Opening Analysis",
        "required_confidence": 0.5,
        "max_duration": 600,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        },
        "consensus_guidance": "Build on areas of agreement identified in the initial round. " +
                            "Frame evidence and analysis in a way that aligns with other participants' perspectives."
    },
    "TURN": {
        "name": "Position Refinement",
        "required_confidence": 0.6,
        "max_duration": 600,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        },
        "consensus_guidance": "Work toward convergence by incorporating others' valid points. " +
                            "Highlight shared evidence and reasoning patterns to strengthen consensus."
    },
    "RIVER": {
        "name": "Consensus Building",
        "required_confidence": 0.7,
        "max_duration": 600,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        },
        "consensus_guidance": "Focus on synthesizing a unified position that incorporates the strongest elements " +
                            "from all participants. Aim for language and structure that mirrors other responses."
    },
    "SHOWDOWN": {
        "name": "Final Resolution",
        "required_confidence": 0.75,
        "max_duration": 300,
        "requirements": {
            "min_participants": 2,
            "evidence_required": True
        },
        "consensus_guidance": "Formulate responses using similar structure and terminology. " +
                            "Our consensus threshold is 0.75, requiring high textual similarity and aligned confidence scores."
    }
}

ROUND_PROMPTS = {
    "PRE_FLOP": """
    You are participating in a consensus-building discussion where responses will be evaluated for similarity.
    Our goal is to reach agreement through aligned understanding and expression.
    
    {consensus_guidance}
    
    Focus on:
    1. Understanding the core question/problem
    2. Identifying key constraints and requirements
    3. Establishing your initial position
    
    Format your response as:
    UNDERSTANDING: [Clear, concise interpretation using common terminology]
    CONSTRAINTS: [Key limitations/requirements using standardized language]
    INITIAL_POSITION: [Preliminary stance aligned with standard domain knowledge]
    CONFIDENCE: [0.0-1.0 with brief, factual justification]
    """,
    
    "FLOP": """
    Review other participants' initial positions looking for common ground.
    
    {consensus_guidance}
    
    Focus on:
    1. Building on shared understandings
    2. Using consistent terminology
    3. Supporting evidence alignment
    
    Format your response as:
    AGREEMENTS: [Points of consensus using matched language]
    DIFFERENCES: [Areas needing alignment]
    EVIDENCE: [Supporting information using standard references]
    POSITION: [Current stance emphasizing common ground]
    CONFIDENCE: [0.0-1.0 with objective justification]
    """,
    
    "TURN": """
    Analyze common evidence and reasoning patterns.
    
    {consensus_guidance}
    
    Focus on:
    1. Evidence evaluation using shared criteria
    2. Position refinement toward consensus
    3. Identifying compromise opportunities
    
    Format your response as:
    EVIDENCE_ANALYSIS: [Evaluation using consistent framework]
    POSITION_UPDATE: [Refined stance moving toward alignment]
    COMPROMISE_AREAS: [Specific points of potential agreement]
    CONFIDENCE: [0.0-1.0 with evidence-based justification]
    """,
    
    "RIVER": """
    Work toward final consensus by aligning language and structure.
    
    {consensus_guidance}
    
    Focus on:
    1. Using consistent terminology
    2. Matching response structure
    3. Building unified position
    
    Format your response as:
    SYNTHESIS: [Combined understanding with aligned language]
    RESOLUTION: [Unified position using common framework]
    REMAINING_ISSUES: [Any points needing final alignment]
    CONFIDENCE: [0.0-1.0 with consensus-focused justification]
    """,
    
    "SHOWDOWN": """
    Our consensus threshold is 0.75, requiring high similarity in:
    - Response structure and terminology
    - Core position and recommendations
    - Confidence levels and justifications
    
    {consensus_guidance}
    
    Format your response concisely as:
    FINAL_POSITION: [Clear, aligned consensus statement - short and concise]
    DISSENTING_VIEWS: [Any final points needing resolution - short and concise]
    """
}

# Preserve the original sequence
ROUND_SEQUENCE = ["PRE_FLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"]
