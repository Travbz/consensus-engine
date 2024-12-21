"""Configuration settings for the Consensus Engine."""
import os
import logging
from typing import Dict, Any

# Model Settings with initialization configuration
MODEL_CONFIGS = {
    "openai": {
        "enabled": True,
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4-turbo-preview",
        "temperature": 0.7,
        "max_tokens": 2000,
        "module_path": "consensus_engine.models.openai",
        "class_name": "OpenAILLM",
        "system_prompt": """You are a cooperative AI participating in a multi-AI consensus discussion. 
        Your goal is to collaboratively identify common ground and efficiently produce a clear, 
        concise, and actionable response to the original query. You will agree on a format to answer and then provide a solution.""",
        "initialization": {
            "required_env_vars": ["OPENAI_API_KEY"],
            "required_packages": ["openai"]
        }
    },
    "anthropic": {
        "enabled": True,
        "api_key_env": "ANTHROPIC_API_KEY",
        "model": "claude-3-sonnet-20240229",
        "temperature": 0.7,
        "max_tokens": 2000,
        "module_path": "consensus_engine.models.anthropic",
        "class_name": "AnthropicLLM",
        "system_prompt": """You are a cooperative AI participating in a multi-AI consensus discussion. 
        Your goal is to collaboratively identify common ground and efficiently produce a clear, 
        concise, and actionable response to the original query. You will agree on a format to answer and then provide a solution.""",
        "initialization": {
            "required_env_vars": ["ANTHROPIC_API_KEY"],
            "required_packages": ["anthropic"]
        }
    },
    "gemini": {
        "enabled": True,
        "api_key_env": "GOOGLE_API_KEY",
        "model": "gemini-1.5-pro",  # Updated to 1.5 Pro
        "temperature": 0.7,
        "max_tokens": 2000,
        "module_path": "consensus_engine.models.gemini",
        "class_name": "GeminiLLM",
        "system_prompt": """You are a cooperative AI participating in a multi-AI consensus discussion. 
        Your goal is to collaboratively identify common ground and efficiently produce a clear, 
        concise, and actionable response to the original query. You will agree on a format to answer and then provide a solution.""",
        "initialization": {
            "required_env_vars": ["GOOGLE_API_KEY"],
            "required_packages": ["google.generativeai"]
        },
        "generation_config": {
            "top_p": 1,
            "top_k": 40,
            "candidate_count": 1,
            "stop_sequences": [],
            "max_output_tokens": 2000
        },
        "safety_settings": {
            "harassment": "block_none",
            "hate_speech": "block_none",
            "sexually_explicit": "block_none",
            "dangerous_content": "block_none"
        },
        "tools": []
    }
}

# Consensus Settings
CONSENSUS_SETTINGS = {
    "max_iterations": 4,
    "consensus_threshold": 0.70,
    "min_models": 2,
    "max_models": 5,
}

# Model-specific settings
GEMINI_SETTINGS = {
    "available_models": [
        "gemini-1.5-pro",  # Updated model list
        "gemini-1.5-pro-vision",
        "gemini-1.5-pro-latest"
    ],
    "max_retries": 3,
    "retry_delay": 1,
    "timeout": 60,  # Increased timeout for the more capable model
    "streaming": False,
    "context_window": 2000000  # 2M token context window
}

# Logging Settings
LOG_LEVEL = os.getenv("CONSENSUS_ENGINE_LOG_LEVEL", "WARNING")
LOG_FORMAT = '%(message)s'
DETAILED_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def get_enabled_models() -> Dict[str, Dict[str, Any]]:
    """Get configurations for all enabled models."""
    return {name: config for name, config in MODEL_CONFIGS.items() if config["enabled"]}

def validate_model_config(config: Dict[str, Any]) -> bool:
    """Validate that a model configuration has all required fields."""
    required_fields = [
        "api_key_env", "model", "temperature", "max_tokens",
        "module_path", "class_name", "system_prompt", "initialization"
    ]
    return all(field in config for field in required_fields)

def get_api_key(config: Dict[str, Any]) -> str:
    """Get API key for a model from environment variables."""
    api_key = os.getenv(config["api_key_env"])
    if not api_key:
        raise ValueError(f"Missing API key: {config['api_key_env']} environment variable not set")
    return api_key

def validate_environment(config: Dict[str, Any]) -> bool:
    """Validate that all required environment variables and packages are available."""
    # Check environment variables
    for env_var in config["initialization"]["required_env_vars"]:
        if not os.getenv(env_var):
            return False
            
    # Check required packages
    for package in config["initialization"]["required_packages"]:
        try:
            __import__(package.split('.')[0])
        except ImportError:
            return False
            
    return True

# Convert string log level to logging constant
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

LOG_LEVEL_NUM = LOG_LEVEL_MAP.get(LOG_LEVEL.upper(), logging.WARNING)