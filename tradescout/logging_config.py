"""Centralized logging configuration for tradescout."""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class TradescoutLogger:
    """Centralized logger for tradescout with file and console output."""
    
    _instance: Optional['TradescoutLogger'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.setup_logging()
            TradescoutLogger._initialized = True
    
    def setup_logging(self, log_level: str = "INFO", log_dir: str = "logs"):
        """Setup logging configuration with both file and console handlers."""
        
        # Create logs directory
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('tradescout')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        
        # File handler with daily rotation
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = log_path / f"tradescout_{today}.log"
        
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        
        # Console handler for errors and warnings
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Log startup message
        self.logger.info("Tradescout logging initialized")
        self.logger.info(f"Log file: {log_file}")
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get logger instance with optional name suffix."""
        if name:
            return logging.getLogger(f'tradescout.{name}')
        return self.logger
    
    def log_and_print(self, message: str, level: str = "INFO", print_msg: bool = True):
        """Log a message and optionally print it to console for user visibility."""
        log_level = getattr(logging, level.upper())
        self.logger.log(log_level, message)
        
        if print_msg:
            print(message)
    
    def debug(self, message: str, print_msg: bool = False):
        """Log debug message."""
        self.log_and_print(message, "DEBUG", print_msg)
    
    def info(self, message: str, print_msg: bool = True):
        """Log info message and optionally print."""
        self.log_and_print(message, "INFO", print_msg)
    
    def warning(self, message: str, print_msg: bool = True):
        """Log warning message and print to console."""
        self.log_and_print(message, "WARNING", print_msg)
    
    def error(self, message: str, print_msg: bool = True):
        """Log error message and print to console."""
        self.log_and_print(message, "ERROR", print_msg)
    
    def critical(self, message: str, print_msg: bool = True):
        """Log critical message and print to console."""
        self.log_and_print(message, "CRITICAL", print_msg)


# Global logger instance
_global_logger = None

def get_logger(name: str = None) -> logging.Logger:
    """Get the global tradescout logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = TradescoutLogger()
    return _global_logger.get_logger(name)

def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """Setup global logging configuration."""
    global _global_logger
    if _global_logger is None:
        _global_logger = TradescoutLogger()
    _global_logger.setup_logging(log_level, log_dir)

def log_and_print(message: str, level: str = "INFO", print_msg: bool = True):
    """Log a message and optionally print it."""
    global _global_logger
    if _global_logger is None:
        _global_logger = TradescoutLogger()
    _global_logger.log_and_print(message, level, print_msg)

# Convenience functions
def debug(message: str, print_msg: bool = False):
    """Log debug message."""
    log_and_print(message, "DEBUG", print_msg)

def info(message: str, print_msg: bool = True):
    """Log info message."""
    log_and_print(message, "INFO", print_msg)

def warning(message: str, print_msg: bool = True):
    """Log warning message."""
    log_and_print(message, "WARNING", print_msg)

def error(message: str, print_msg: bool = True):
    """Log error message."""
    log_and_print(message, "ERROR", print_msg)

def critical(message: str, print_msg: bool = True):
    """Log critical message."""
    log_and_print(message, "CRITICAL", print_msg)