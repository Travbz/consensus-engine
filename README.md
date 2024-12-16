# Consensus Engine

A sophisticated tool for orchestrating structured discussions between multiple Large Language Models (LLMs) to reach consensus through a round-based deliberation process.

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

## Project Structure

```
consensus-engine/
├── src/
│   └── consensus_engine/
│       ├── config/          # Configuration files
│       ├── models/          # LLM implementations
│       ├── database/        # Database models
│       └── protocols/       # Consensus protocols
├── tests/                   # Test suite
└── examples/                # Usage examples
```

## Round-Based Discussion Flow

1. **PRE_FLOP**:
   - Initial problem understanding
   - Constraint identification
   - Preliminary position establishment

2. **FLOP**:
   - Evidence presentation
   - Initial agreement areas
   - Key differences identification

3. **TURN**:
   - Evidence analysis
   - Position refinement
   - Compromise exploration

4. **RIVER**:
   - Final position synthesis
   - Resolution of differences
   - Consensus building

5. **SHOWDOWN**:
   - Final position statement
   - Implementation details
   - Any remaining disagreements

## Contributing

1. Fork the repository
2. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

3. Make your changes and commit:
```bash
git commit -m "Add your feature description"
```

4. Push to your fork:
```bash
git push origin feature/your-feature-name
```

5. Create a Pull Request

### Development Setup

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

## Response Format

LLMs are prompted to provide structured responses:

```
UNDERSTANDING: [Problem interpretation]
CONSTRAINTS: [Key limitations]
POSITION: [Current stance]
CONFIDENCE: [0.0-1.0 with justification]
EVIDENCE: [Supporting information]
```

## Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Verify environment variables are set
   - Check API key validity
   - Ensure sufficient API credits

2. **NLTK Resource Errors**:
   - The package automatically downloads required NLTK data
   - Manual download: `python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"`

3. **Port Conflicts**:
   - Default port (7860) in use: Use `--port` to specify different port
   - Permission denied: Try a port number > 1024

### Debug Mode

Enable debug logging:
```bash
export CONSENSUS_ENGINE_LOG_LEVEL=DEBUG
consensus-engine --debug
```

## License

MIT License - see LICENSE file for details

## Documentation

- `config/settings.py`: Configuration options
- `docs/`: Detailed documentation (coming soon)
- `examples/`: Usage examples
- `tests/README.md`: Testing documentation

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

## Contact

- Issues: Use GitHub Issues
- Questions: Start a GitHub Discussion
- Security concerns dial 911
