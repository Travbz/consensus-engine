"""Initialize NLTK resources after package installation."""
import os
import logging

logger = logging.getLogger(__name__)

def initialize():
    """Download required NLTK resources."""
    try:
        # Now that we're running post-installation, we can safely import nltk
        import nltk
        
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
        
        print("NLTK resources initialized successfully!")
        
    except Exception as e:
        logger.warning(f"NLTK initialization failed: {e}")
        print(f"Error initializing NLTK resources: {e}")

if __name__ == "__main__":
    initialize()