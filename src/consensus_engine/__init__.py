"""Initialize NLTK resources and setup for consensus engine."""
import os
import logging
import nltk

logger = logging.getLogger(__name__)

def setup_nltk():
    """Download and set up required NLTK resources."""
    try:
        # Create NLTK data directory in user's home
        nltk_data_dir = os.path.join(os.path.expanduser("~"), "nltk_data")
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        # Download required resources
        for resource in ['punkt', 'stopwords']:
            try:
                nltk.download(resource, quiet=True, download_dir=nltk_data_dir)
                logger.info(f"Successfully downloaded {resource}")
            except Exception as e:
                logger.warning(f"Failed to download {resource}: {e}")
                continue
        
        logger.info("NLTK resources initialized successfully!")
        return True
        
    except Exception as e:
        logger.warning(f"NLTK initialization failed: {e}")
        return False

# Run setup when module is imported
setup_nltk()