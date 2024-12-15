"""Model loader for dynamic LLM initialization."""
import importlib
import logging
from typing import List, Type
from .base import BaseLLM
from ..config.settings import get_enabled_models, validate_model_config, get_api_key

logger = logging.getLogger(__name__)

class ModelLoader:
    """Dynamic model loader for LLMs."""
    
    @staticmethod
    def load_models() -> List[BaseLLM]:
        """Load all enabled and properly configured models."""
        models = []
        enabled_configs = get_enabled_models()
        
        for model_name, config in enabled_configs.items():
            try:
                if not validate_model_config(config):
                    logger.warning(f"Invalid configuration for {model_name}, skipping")
                    continue
                
                # Get API key
                try:
                    api_key = get_api_key(config)
                except ValueError as e:
                    logger.warning(f"Skipping {model_name}: {str(e)}")
                    continue
                
                # Import the model module
                module = importlib.import_module(config["module_path"])
                model_class: Type[BaseLLM] = getattr(module, config["class_name"])
                
                # Initialize the model
                model = model_class(
                    api_key=api_key,
                    model=config["model"],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"],
                    system_prompt=config["system_prompt"]
                )
                
                models.append(model)
                logger.info(f"Successfully loaded {model_name} model")
                
            except Exception as e:
                logger.warning(f"Failed to load {model_name} model: {str(e)}")
                continue
        
        return models

    @staticmethod
    def validate_models(models: List[BaseLLM]) -> bool:
        """Validate that we have enough models for consensus."""
        from ..config.settings import CONSENSUS_SETTINGS
        
        min_models = CONSENSUS_SETTINGS["min_models"]
        max_models = CONSENSUS_SETTINGS["max_models"]
        
        if len(models) < min_models:
            logger.error(f"Not enough models loaded. Minimum required: {min_models}")
            return False
            
        if len(models) > max_models:
            logger.warning(f"Too many models loaded. Using first {max_models}")
            del models[max_models:]
            
        return True