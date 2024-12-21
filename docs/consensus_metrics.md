# Consensus Metrics and Process

## Overview
The consensus engine evaluates agreement between LLMs using a combination of semantic similarity measures and confidence scoring. Each round builds upon previous discussions to reach a final consensus.

## Core Metrics

1. **Semantic Similarity**
   - TF-IDF vectorization of responses
   - Cosine similarity calculation
   - Automatic handling of common stopwords
   - Fallback to simpler text comparison when needed

2. **Confidence Scoring**
   - Self-reported confidence (0.0-1.0)
   - Aggregated across all participating LLMs
   - Weighted by response similarity
   - Required thresholds increase by round

## Round Structure and Evolution

The consensus process follows a poker-inspired round structure:

1. **PRE_FLOP**: Initial Understanding
   - Problem interpretation
   - Constraint identification
   - Base confidence: 0.0

2. **FLOP**: Opening Analysis
   - Format proposal
   - Initial solution
   - Required confidence: 0.5

3. **TURN**: Position Refinement
   - Format agreement
   - Solution refinement
   - Required confidence: 0.6

4. **RIVER**: Consensus Building
   - Implementation in agreed format
   - Format adherence
   - Required confidence: 0.7

5. **SHOWDOWN**: Final Resolution
   - Strict format compliance
   - Final solution only
   - Required confidence: 0.75

## Conversation History

Each LLM receives a complete conversation history that includes:

1. **Original Prompt Context**
   - Initial query
   - Any provided constraints
   - Special format requirements

2. **Round-by-Round Evolution**
   - All previous responses from each LLM
   - Round labels for context
   - Format changes and agreements
   - Example:
     ```
     Original prompt: [Query]

     === PRE_FLOP ROUND ===
     LLM1: [Response]
     LLM2: [Response]
     LLM3: [Response]

     === FLOP ROUND ===
     LLM1: [Response]
     LLM2: [Response]
     LLM3: [Response]
     ```

3. **Consensus Metrics History**
   - Similarity scores by round
   - Confidence trends
   - Format evolution

## Similarity Calculation Details

1. **Text Preprocessing**
   - Lowercase conversion
   - Stopword removal (using NLTK)
   - Section-specific extraction when relevant

2. **Vectorization Process**
   - TF-IDF vectorization (max 1000 features)
   - Cosine similarity computation
   - Normalized scoring (0.0-1.0)

3. **Fallback Mechanisms**
   - Direct sequence matching
   - Common word ratio calculation
   - Ensures robustness when vectorization fails

## Usage Notes

1. **Confidence Thresholds**
   - Increase progressively through rounds
   - Must be met alongside similarity scores
   - Both metrics required for consensus

2. **Format Compliance**
   - Becomes stricter in later rounds
   - Impacts confidence scoring
   - Essential for final consensus

3. **Response Evolution**
   - Early rounds allow format exploration
   - Middle rounds focus on alignment
   - Final rounds require strict compliance