"""Configuration settings for the Consensus Engine."""
import os
import logging
from typing import Dict, Any

# Model Settings, can add another model by adding a new key to the dictionary
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
        concise, and actionable response to the original query."""
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
        concise, and actionable response to the original query."""
    }
}

# Consensus Settings
CONSENSUS_SETTINGS = {
    "max_iterations": 4,
    "consensus_threshold": 0.75,
    "min_models": 2,
    "max_models": 5,
}

# Logging Settings
LOG_LEVEL = os.getenv("CONSENSUS_ENGINE_LOG_LEVEL", "INFO")
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
        "module_path", "class_name", "system_prompt"
    ]
    return all(field in config for field in required_fields)

def get_api_key(config: Dict[str, Any]) -> str:
    """Get API key for a model from environment variables."""
    api_key = os.getenv(config["api_key_env"])
    if not api_key:
        raise ValueError(f"Missing API key: {config['api_key_env']} environment variable not set")
    return api_key

# Convert string log level to logging constant
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

LOG_LEVEL_NUM = LOG_LEVEL_MAP.get(LOG_LEVEL.upper(), logging.INFO)