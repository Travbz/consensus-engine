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

consensus-engine-init

```

## Usage
* navigate to consensus-engine/src/consensus_engine/config/settings.py and set your API keys
* Update system prompts to your liking
* Modify token usage limits to your liking
* Modify deliberation parameters to your liking


### Command Line Interface
```bash
# Set your API keys
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"

# Run the CLI
consensus-engine discuss

# Launch web interface
consensus-engine --web --port 8080

# List past discussions
consensus-engine --list

# View specific discussion
consensus-engine --view 1

# Start CLI discussion
consensus-engine --cli

# Default to CLI mode if no flags
consensus-engine


```

Then open http://localhost:7860 (or your specified port) in your browser.