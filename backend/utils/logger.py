import logging
import sys

def setup_logger(name: str = "candidate_transformer") -> logging.Logger:
    """Configures and returns a standard logger for the application.
    
    Args:
        name (str): Name of the logger.
        
    Returns:
        logging.Logger: The configured Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Simple formatter to print exactly: LEVEL Message (e.g. INFO Reading CSV)
        formatter = logging.Formatter('%(levelname)s %(message)s')
        
        # Output to stdout as requested
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

# Singleton-like logger instance for convenient project-wide importing
logger = setup_logger()
