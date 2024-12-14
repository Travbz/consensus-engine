"""Configuration settings for the Consensus Engine."""
import os
import logging

# Model Settings
OPENAI_CONFIG = {
    "model": "gpt-4-turbo-preview",
    "temperature": 0.7,
    "max_tokens": 2000,
    "system_prompt": "You are a cooperative AI participating in a multi-AI consensus discussion. Your goal is to find common ground and agree efficiently."
}

ANTHROPIC_CONFIG = {
    "model": "claude-3-sonnet-20240229",
    "temperature": 0.7,
    "max_tokens": 2000,
    "system_prompt": "You are a cooperative AI participating in a multi-AI consensus discussion. Your goal is to find common ground and agree efficiently."

}

# Consensus Settings
MAX_ITERATIONS = 4
CONSENSUS_THRESHOLD = 0.75

# System Prompts for Different Stages
DELIBERATION_PROMPT = """You are tasked with analyzing the provided responses to identify common ground and propose a unified solution that satisfies the original query. 

- Focus on the core objective of the query and provide a concise, actionable, and user-centric response.
- Avoid philosophical debates or excessive elaboration; prioritize clarity and simplicity.
- Highlight the strengths of each response, resolve any conflicting points, and synthesize a response that directly addresses the user's needs.
- Ensure the final response is easy to understand, aligns with the original query, and offers a practical solution."""

# Database Settings
DATABASE_URL = os.getenv("CONSENSUS_ENGINE_DB_URL", "sqlite:///consensus_engine.db")

# Logging Settings
LOG_LEVEL = os.getenv("CONSENSUS_ENGINE_LOG_LEVEL", "INFO")
LOG_FORMAT = '%(message)s'
DETAILED_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Convert string log level to logging constant
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

LOG_LEVEL_NUM = LOG_LEVEL_MAP.get(LOG_LEVEL.upper(), logging.INFO)