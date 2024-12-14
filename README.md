# Consensus Engine

A tool for orchestrating discussions between multiple LLMs to reach consensus.

## Features

	•	Multi-LLM consensus-building framework.
	•	Supports OpenAI and Anthropic LLMs.
	•	CLI and Gradio-based web interface.
	•	Persistent storage for discussions (SQLite by default).
	•	Modular design for extensibility.

## Prerequisites

	•	Python 3.8 or later
	•	Git
	•	API keys for OpenAI and Anthropic models
	•	SQLite (bundled with Python standard library)

## Installation



```bash
git clone git@github.com:Travbz/consensus-engine.git

cd consensus-engine

python3 -m venv venv

source venv/bin/activate

pip install -e .
```

## Usage

### Command Line Interface
```bash
# Set your API keys
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"

# Run the CLI
consensus-engine discuss
```

### Web Interface (Gradio)
```bash
# Run the web interface
consensus-web

# Or with custom port
consensus-web --port 8080

# Or with specific host
consensus-web --host 0.0.0.0 --port 8080

# For CLI with debug output
consensus-engine discuss --debug

# For web interface
consensus-engine web --port 8080 --debug

# To view a past discussion
consensus-engine view-discussion 1 --debug

```

Then open http://localhost:7860 (or your specified port) in your browser.