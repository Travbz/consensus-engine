# Consensus Engine - Technical Documentation

This document provides a detailed technical overview of how the Consensus Engine works internally. For basic setup and usage, see the main README.md in the root directory.

## Core Components and Implementation Details

### 1. Consensus Determination

#### TF-IDF Vectorization
Term Frequency-Inverse Document Frequency (TF-IDF) is a numerical statistic that reflects how important a word is within a response. It works by:

1. **Term Frequency (TF)**:
   - Counts how often a word appears in a response
   - Normalized by response length
   - Example: If "algorithm" appears 3 times in a 100-word response, TF = 0.03

2. **Inverse Document Frequency (IDF)**:
   - Measures how unique a word is across all responses
   - Words appearing in all responses get lower weight
   - Example: Common words like "the" get very low IDF scores

3. **Final TF-IDF Score**:
   - Multiplies TF × IDF
   - High scores indicate words that are both frequent in this response and unique across responses
   - Creates a numerical vector representing each response

#### Cosine Similarity Calculation
After TF-IDF creates vectors, cosine similarity measures their alignment:

1. **Vector Representation**:
   - Each response becomes a vector in high-dimensional space
   - Each dimension represents a unique word
   - Values are TF-IDF scores

2. **Similarity Computation**:
   - Calculates the cosine of the angle between vectors
   - Range: 0 (completely different) to 1 (identical)
   - Formula: cos(θ) = (A·B) / (||A|| ||B||)

Example:
```python
Response 1: "The quick brown fox"
Response 2: "The quick brown dog"
# After TF-IDF and cosine similarity:
# Result might be 0.85 (very similar but not identical)
```

#### Code Similarity Metrics
When responses contain code, additional metrics are applied:

1. **Structural Similarity**:
   - Abstract Syntax Tree (AST) comparison
   - Function signature matching
   - Control flow analysis
   - Example: Two functions with same parameters and return types but different variable names would have high structural similarity

2. **Naming Pattern Analysis**:
   - Variable/function name comparison
   - Naming convention consistency
   - Camel case vs. snake case detection

3. **Logic Flow Comparison**:
   - Control structure alignment
   - Error handling patterns
   - Algorithm steps matching

Example:
```python
# These would have high similarity despite superficial differences
def calculate_area(length, width):
    return length * width

def get_area(l, w):
    return l * w
```

#### Evidence Overlap Analysis
Measures how much supporting evidence is shared between responses:

1. **Citation Matching**:
   - Identifies referenced sources
   - Compares citation overlap
   - Weights by citation importance
   - Example: Two responses citing the same academic paper would increase similarity

2. **Fact Alignment**:
   - Extracts key facts and statistics
   - Compares numerical values
   - Checks unit consistency
   - Example: Both responses mentioning "73% improvement" would increase similarity

3. **Example Comparison**:
   - Identifies illustrative examples
   - Compares example structures
   - Analyzes example relevance

### Similarity Weight Implementation

#### Current Implementation
The system currently uses an adaptive averaging approach:

1. Starts with base TF-IDF similarity score
2. When code is present: 
   - Averages base similarity with code similarity (50/50 split)
3. When evidence is present:
   - Averages current similarity with evidence similarity (50/50 split)

Example:
```python
# Starting similarity: 0.8
# With code similarity of 0.6:
# (0.8 + 0.6) / 2 = 0.7 final similarity

# If evidence (0.9) also present:
# (0.7 + 0.9) / 2 = 0.8 final similarity
```

#### Future Goals
Future versions aim to implement context-aware weighting:

For different types of discussions:
- Code-heavy responses: w2 = 0.6 (emphasize code similarity)
- Research discussions: w3 = 0.5 (balance evidence with semantic similarity)
- General discussions: w1 = 0.7 (prioritize semantic similarity)

This would allow the system to adapt its similarity calculations based on the type of content being analyzed, providing more accurate consensus measurements for different discussion types.

### 2. Round System Implementation

The round system is inspired by poker game structure:

#### PRE_FLOP
- Entry point for discussion
- Purpose: Establish initial understanding and constraints
- No similarity threshold required
- Focus on problem interpretation
- Key outputs: Problem constraints, initial positions

#### FLOP
- First major discussion round
- Purpose: Present evidence and initial positions
- Minimum similarity: 0.5
- Focus on evidence presentation
- Key outputs: Initial agreements, key differences

#### TURN
- Refinement round
- Purpose: Analyze evidence and refine positions
- Minimum similarity: 0.6
- Focus on compromise exploration
- Key outputs: Updated positions, compromise areas

#### RIVER
- Consensus building round
- Purpose: Final position synthesis
- Minimum similarity: 0.7
- Focus on resolving differences
- Key outputs: Near-final positions, resolution paths

#### SHOWDOWN
- Final resolution round
- Purpose: Implementation details
- Minimum similarity: 0.75
- Focus on practical application
- Key outputs: Final consensus, implementation plan

### 3. Database Schema

#### Discussion Table
```sql
CREATE TABLE discussions (
    id INTEGER PRIMARY KEY,
    prompt TEXT NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    consensus_reached INTEGER DEFAULT 0,
    final_consensus TEXT
);
```

#### DiscussionRound Table
```sql
CREATE TABLE discussion_rounds (
    id INTEGER PRIMARY KEY,
    discussion_id INTEGER,
    round_number INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(discussion_id) REFERENCES discussions(id)
);
```

#### LLMResponse Table
```sql
CREATE TABLE llm_responses (
    id INTEGER PRIMARY KEY,
    round_id INTEGER,
    llm_name VARCHAR(100) NOT NULL,
    response_text TEXT NOT NULL,
    confidence_score FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(round_id) REFERENCES discussion_rounds(id)
);
```

### 4. Error Handling and Recovery

The system implements several layers of error handling:

1. **API Layer**
   - Retries on temporary failures
   - Graceful degradation on model unavailability
   - Rate limit handling
   - Timeout management

2. **Response Validation**
   - Format checking
   - Confidence score validation
   - Content structure verification
   - Required field presence

3. **Round Management**
   - State consistency checks
   - Transaction rollback on failures
   - Partial result handling
   - Recovery from incomplete rounds

4. **Database Operations**
   - Transaction integrity
   - Constraint validation
   - Foreign key maintenance
   - Concurrent access handling

### 5. Performance Considerations

The system is optimized for:

1. **Concurrent Operations**
   - Async/await pattern usage
   - Connection pooling
   - Resource sharing
   - Lock minimization

2. **Memory Management**
   - Streaming response handling
   - Efficient vector operations
   - Garbage collection optimization
   - Memory-mapped file usage

3. **CPU Efficiency**
   - Vectorized calculations
   - Cached similarity scores
   - Optimized text processing
   - Lazy evaluation patterns

4. **I/O Optimization**
   - Batched database operations
   - Buffered file operations
   - Compressed storage
   - Connection reuse