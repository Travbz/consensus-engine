# Consensus Engine

A sophisticated tool for orchestrating structured discussions between multiple Large Language Models (LLMs) to reach consensus through a round-based deliberation process using prompt chaining.

## Features

- **Round-Based Consensus Protocol**: Implements a poker-style discussion format
  - PRE_FLOP: Initial setup and position establishment
  - FLOP: Opening statements and evidence presentation
  - TURN: Evidence analysis and position refinement
  - RIVER: Final consensus building
  - SHOWDOWN: Resolution and implementation details

- **Multiple LLM Support**:
  - OpenAI GPT-4 integration
  - Anthropic Claude integration
  - Extensible architecture for adding new models

- **Robust Discussion Management**:
  - Confidence scoring
  - Semantic similarity analysis
  - Structured response formats

- **Multiple Interfaces**:
  - Command-line interface
  - Web interface (Gradio-based)
  - API for custom integration

## Prerequisites

- Python 3.8 or later
- OpenAI API key
- Anthropic API key
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/travbz/consensus-engine.git
cd consensus-engine
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

## Configuration

1. Set up environment variables:
```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

2. Optional: Configure model settings in `src/consensus_engine/config/settings.py`:
- Model selection
- Temperature settings
- Token limits
- System prompts

## Usage

### Command Line Interface

1. Start a discussion:
```bash
consensus-engine
```

2. View past discussions:
```bash
consensus-engine --list
```

3. View specific discussion:
```bash
consensus-engine --view <discussion_id>
```

4. Enable debug logging:
```bash
consensus-engine --debug
```

### Web Interface

1. Start the web server:
```bash
consensus-engine --web
```

2. Optional: Specify port and host:
```bash
consensus-engine --web --port 8080 --host 0.0.0.0
```

3. Access the interface at `http://localhost:7860` (or your specified port)

### Example Discussion

```bash
$ consensus-engine
Enter your prompt: What is the best way to learn programming?

🚀 Starting consensus discussion...
📍 Starting PRE_FLOP round...
🤖 OpenAI thinking...
🤖 Anthropic thinking...
...
```

## Testing

Run the test suite:
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock pytest-cov

# Run all tests
pytest

# Run specific test categories
pytest -m "not integration"  # Unit tests only
pytest -m integration       # Integration tests only
pytest tests/test_interfaces.py  # Interface tests
```

See `/tests/README.md` for detailed testing documentation.



## Overview

The Consensus Engine is a sophisticated system designed to orchestrate structured discussions between multiple Large Language Models (LLMs) to reach consensus through a round-based deliberation process. This document explains how each component works and interacts within the system.

## Core Components

### 1. Engine (`engine.py`)
The main orchestrator of the consensus process. It:
- Manages the flow of discussion rounds with a form of prompt chaining
- Tracks and evaluates consensus through similarity metrics
- Coordinates between different LLMs
- Handles database persistence
- Provides progress updates

Key features:
- Semantic similarity calculation using TF-IDF and cosine similarity
- Confidence score extraction and validation
- Consensus threshold enforcement (default 0.75)
- Progress tracking and callback system

### 2. Models (`models/`)
The Models layer handles interactions with different LLM providers:

- `base.py`: Abstract base class defining the LLM interface
- `openai.py`: OpenAI (GPT-4) implementation
- `anthropic.py`: Anthropic (Claude) implementation
- `loader.py`: Dynamic model loading and configuration

Each model implementation:
- Manages API connections
- Handles response generation
- Provides consistent interface for the engine
- Implements proper error handling

### 3. Round System (`config/round_config.py`)
Implements a poker-style discussion format with five rounds:

1. **PRE_FLOP**: Initial Understanding
   - Problem interpretation
   - Constraint identification
   - Initial position establishment
   - No confidence requirement (0.0)

2. **FLOP**: Opening Analysis
   - Evidence presentation
   - Initial agreements identified
   - Key differences noted
   - Minimum confidence: 0.5

3. **TURN**: Position Refinement
   - Evidence analysis
   - Position updates
   - Compromise exploration
   - Minimum confidence: 0.6

4. **RIVER**: Consensus Building
   - Final position synthesis
   - Difference resolution
   - Consensus building
   - Minimum confidence: 0.7

5. **SHOWDOWN**: Final Resolution
   - Implementation details
   - Final position statement
   - Minimum confidence: 0.75

### 4. Database (`database/`)
SQLAlchemy-based persistence layer:

- `Discussion`: Tracks complete discussions
- `DiscussionRound`: Individual round information
- `LLMResponse`: Individual LLM responses
- SQLite by default with support for other databases

### 5. Interfaces

#### CLI (`cli.py`)
Command-line interface supporting:
- Interactive discussions
- Discussion history viewing
- Debug mode
- Configuration options

#### Web Interface (`web.py`)
Gradio-based web interface providing:
- Discussion visualization
- Discussion history
- Export capabilities

## Configuration

Major configuration areas:

1. Model Settings (`config/settings.py`)
   - API keys and endpoints
   - Model parameters
   - Temperature settings
   - Token limits

2. Round Settings (`config/round_config.py`)
   - Round sequence
   - Confidence requirements
   - Time limits
   - Response formats

3. Consensus Settings
   - Similarity thresholds
   - Minimum model requirements
   - Maximum iterations
   - Success criteria

## Response Format

LLMs must provide structured responses following this format(Varies by round):

```
UNDERSTANDING: [Problem interpretation]
CONSTRAINTS: [Key limitations]
POSITION: [Current stance]
CONFIDENCE: [0.0-1.0 with justification]
EVIDENCE: [Supporting information]
```

## Error Handling

The system implements robust error handling:
- API failure recovery
- Response validation
- Format enforcement
- Round progression safety checks
- Database transaction management

## Testing

Tests covering:
- Core engine functionality
- Model implementations
- Round management
- Interface behavior
- Integration scenarios

## Performance and Scalability

The system is designed for:
- Asynchronous operation
- Multiple concurrent discussions
- Dynamic model loading
- Efficient similarity calculations
- Persistent storage
## Citing

If you use Consensus Engine in your research, please cite:

```bibtex
@software{consensus_engine,
  title = {Consensus Engine},
  author = {Travis Bridle},
  year = {2024},
  url = {https://github.com/Travbz/consensus-engine}
}
```