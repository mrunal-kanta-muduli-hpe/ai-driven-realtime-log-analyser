"""
Logging Utilities Module

Provides centralized logging configuration and utilities for the Smart Log Analyzer.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None, log_dir: str = "logs") -> None:
    """
    Setup application logging with both console and file handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional specific log file name
        log_dir: Directory for log files
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Set up log file name
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = f"smart_log_analyzer_{timestamp}.log"
    
    log_file_path = log_path / log_file
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(simple_formatter)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
    file_handler.setFormatter(detailed_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Log the configuration
    logging.info(f"Logging configured - Level: {log_level}, File: {log_file_path}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_function_call(func):
    """
    Decorator to log function calls with parameters and execution time.
    
    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            pass
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # Log function entry
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    return wrapper


def log_performance(operation_name: str):
    """
    Context manager for logging operation performance.
    
    Usage:
        with log_performance("data_processing"):
            # do some work
            pass
    """
    import time
    from contextlib import contextmanager
    
    @contextmanager
    def performance_logger():
        logger = get_logger(__name__)
        logger.info(f"Starting {operation_name}")
        start_time = time.time()
        
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            logger.info(f"Completed {operation_name} in {execution_time:.3f}s")
    
    return performance_logger()


class StructuredLogger:
    """
    Structured logger for consistent log formatting across the application.
    """
    
    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = get_logger(name)
    
    def log_analysis_start(self, file_path: str, component: Optional[str] = None):
        """Log analysis start event."""
        self.logger.info(
            f"Analysis started - File: {file_path}" + 
            (f", Component: {component}" if component else "")
        )
    
    def log_analysis_complete(self, file_path: str, results: dict):
        """Log analysis completion with results."""
        self.logger.info(
            f"Analysis completed - File: {file_path}, "
            f"Entries: {results.get('total_entries', 0)}, "
            f"Errors: {results.get('error_count', 0)}, "
            f"Patterns: {results.get('patterns_detected', 0)}"
        )
    
    def log_pattern_detected(self, pattern_type: str, pattern_id: str, frequency: int):
        """Log pattern detection event."""
        self.logger.info(
            f"Pattern detected - Type: {pattern_type}, "
            f"ID: {pattern_id}, Frequency: {frequency}"
        )
    
    def log_defect_generated(self, defect_title: str, severity: str, component: Optional[str] = None):
        """Log defect generation event."""
        self.logger.info(
            f"Defect generated - Title: {defect_title}, "
            f"Severity: {severity}" +
            (f", Component: {component}" if component else "")
        )
    
    def log_ml_training(self, model_type: str, training_samples: int, accuracy: Optional[float] = None):
        """Log ML model training event."""
        accuracy_str = f", Accuracy: {accuracy:.3f}" if accuracy else ""
        self.logger.info(
            f"ML training - Model: {model_type}, "
            f"Samples: {training_samples}{accuracy_str}"
        )
    
    def log_error_with_context(self, error: Exception, context: dict):
        """Log error with additional context."""
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        self.logger.error(f"Error: {error} - Context: {context_str}")
    
    def log_performance_metrics(self, operation: str, metrics: dict):
        """Log performance metrics."""
        metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
        self.logger.info(f"Performance - Operation: {operation}, Metrics: {metrics_str}")


def configure_third_party_loggers():
    """Configure logging levels for third-party libraries."""
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("jira").setLevel(logging.WARNING)
    logging.getLogger("sklearn").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


def setup_development_logging():
    """Setup logging configuration optimized for development."""
    setup_logging(
        log_level="DEBUG",
        log_file="development.log"
    )
    configure_third_party_loggers()


def setup_production_logging():
    """Setup logging configuration optimized for production."""
    setup_logging(
        log_level="INFO",
        log_file="production.log"
    )
    configure_third_party_loggers()


# Application-specific loggers
def get_analysis_logger() -> StructuredLogger:
    """Get logger for analysis operations."""
    return StructuredLogger("analysis")


def get_ml_logger() -> StructuredLogger:
    """Get logger for machine learning operations."""
    return StructuredLogger("ml")


def get_integration_logger() -> StructuredLogger:
    """Get logger for integration operations."""
    return StructuredLogger("integration")


# Utility functions for common logging patterns
def log_file_processing(file_path: str, entries_count: int, errors_count: int):
    """Log file processing summary."""
    logger = get_logger(__name__)
    logger.info(
        f"File processed - Path: {file_path}, "
        f"Entries: {entries_count}, Errors: {errors_count}, "
        f"Error rate: {(errors_count/entries_count*100):.1f}%" if entries_count > 0 else "Error rate: 0%"
    )


def log_system_info():
    """Log system information for debugging."""
    import platform
    import psutil
    
    logger = get_logger(__name__)
    logger.info(f"System info - Platform: {platform.platform()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Memory available: {psutil.virtual_memory().available / (1024**3):.1f}GB")
    logger.info(f"CPU count: {psutil.cpu_count()}")


# Exception handling utilities
class LoggingException(Exception):
    """Custom exception that logs itself when raised."""
    
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.context = context or {}
        
        logger = get_logger(__name__)
        logger.error(f"Exception raised: {message}, Context: {self.context}")


def handle_and_log_exception(func):
    """Decorator to catch and log exceptions with context."""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = get_logger(func.__module__)
            logger.error(
                f"Exception in {func.__name__}: {e}, "
                f"Args: {args}, Kwargs: {kwargs}",
                exc_info=True
            )
            raise
    
    return wrapper
