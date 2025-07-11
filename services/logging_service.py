"""Logging service for imgmaster."""

import logging
import sys


class LoggingService:
    """Service for setting up and managing logging."""
    
    @staticmethod
    def setup_logging(verbose: bool = False) -> None:
        """Set up logging configuration."""
        level = logging.DEBUG if verbose else logging.INFO
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(console_handler)
        
        # Set specific loggers
        logging.getLogger('models').setLevel(level)
        logging.getLogger('services').setLevel(level)
