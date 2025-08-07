"""
Logging configuration for AI Driven Realtime Log Analyser
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    debug: bool = False,
    log_file: Optional[str] = None,
    enable_colors: bool = True
):
    """
    Setup logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARN, ERROR)
        debug: Enable debug mode
        log_file: Optional log file path
        enable_colors: Enable colored output
    """
    
    # Set level
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    if enable_colors and sys.stdout.isatty():
        formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


class ColoredFormatter(logging.Formatter):
    """Colored log formatter"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        
        # Format the message
        formatted = super().format(record)
        
        # Add emoji for different log levels
        if 'ERROR' in record.levelname:
            formatted = f"❌ {formatted}"
        elif 'WARNING' in record.levelname:
            formatted = f"⚠️ {formatted}"
        elif 'INFO' in record.levelname:
            formatted = f"ℹ️ {formatted}"
        elif 'DEBUG' in record.levelname:
            formatted = f"🔍 {formatted}"
        
        return formatted


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)
