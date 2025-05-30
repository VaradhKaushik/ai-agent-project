import logging
import sys
from .config import get_config

def setup_logging():
    """Sets up basic logging for the application."""
    config = get_config()
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO').upper()
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout) # Log to stdout
        ]
    )
    # Suppress overly verbose logs from common libraries if needed
    logging.getLogger("httpx").setLevel(logging.WARNING) # httpx can be noisy with Ollama
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("chromadb.telemetry.posthog").setLevel(logging.WARNING) # Chroma telemetry

def get_logger(name: str) -> logging.Logger:
    """Returns a logger instance."""
    return logging.getLogger(name)

if __name__ == '__main__':
    setup_logging()
    logger = get_logger(__name__)
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.") 