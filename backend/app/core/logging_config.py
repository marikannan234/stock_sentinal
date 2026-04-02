"""
Production-level logging configuration for Stock Sentinel API.

Features:
  - Centralized logger setup
  - Console + File logging
  - Structured log format with timestamps
  - Environment-based configuration
  - Request tracking via correlation IDs
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.config import settings


# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
LOG_FILE = LOGS_DIR / "app.log"
ERROR_LOG_FILE = LOGS_DIR / "errors.log"
ACCESS_LOG_FILE = LOGS_DIR / "access.log"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    # ANSI color codes
    COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        if sys.stdout.isatty():  # Only use colors in interactive terminals
            levelno = record.levelno
            if levelno in self.COLORS:
                record.levelname = f"{self.COLORS[levelno]}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging() -> None:
    """
    Configure application-wide logging with structured format.
    
    This function should be called once during application startup.
    
    Logging configuration:
      - Console Handler: INFO level (colored output)
      - File Handler: DEBUG level (all logs)
      - Error Handler: ERROR level (errors only)
      - Access Handler: INFO level (HTTP requests)
    
    Log Format:
      [TIMESTAMP] [LEVEL] [MODULE:FUNCTION:LINE] - MESSAGE
    
    Example:
      >>> setup_logging()
      >>> logger = logging.getLogger(__name__)
      >>> logger.info("Application started")
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Log format with detailed info
    log_format = (
        "[%(asctime)s] [%(levelname)-8s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # ============================================
    # 1. Console Handler (INFO level + colors)
    # ============================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG)
    
    # Use colored formatter for console
    colored_formatter = ColoredFormatter(log_format, datefmt=date_format)
    console_handler.setFormatter(colored_formatter)
    root_logger.addHandler(console_handler)
    
    # ============================================
    # 2. File Handler (all logs to app.log)
    # ============================================
    # Use simple FileHandler instead of RotatingFileHandler to avoid
    # file locking issues on Windows with uvicorn --reload
    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # ============================================
    # 3. Error Handler (ERROR level to errors.log)
    # ============================================
    # Use simple FileHandler instead of RotatingFileHandler to avoid
    # file locking issues on Windows with uvicorn --reload
    error_handler = logging.FileHandler(
        ERROR_LOG_FILE,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # ============================================
    # 4. Access Handler (HTTP requests)
    # ============================================
    # Use simple FileHandler instead of RotatingFileHandler to avoid
    # file locking issues on Windows with uvicorn --reload
    access_handler = logging.FileHandler(
        ACCESS_LOG_FILE,
        encoding="utf-8"
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(formatter)
    
    # Create separate logger for access logs
    access_logger = logging.getLogger("access")
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    
    # ============================================
    # Silence noisy third-party loggers
    # ============================================
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized | Environment: {settings.ENVIRONMENT} | "
        f"Debug: {settings.DEBUG} | Logs: {LOGS_DIR}"
    )


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance for the given module name.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Something important")
    """
    return logging.getLogger(name)


class RequestContextFilter(logging.Filter):
    """
    Add request context to log records (correlation ID, request ID, etc.)
    
    Usage:
        filter = RequestContextFilter()
        handler.addFilter(filter)
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        # This can be extended to add request context from context vars
        # For now, it's a placeholder for future enhancement
        return True
