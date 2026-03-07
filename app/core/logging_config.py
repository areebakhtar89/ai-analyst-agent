"""Centralized logging configuration for the AI Analyst Agent.

This module provides a consistent logging setup across all components
of the application with structured logging and appropriate log levels.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler


# Log configuration - can be overridden by environment variables
LOG_DIR = os.environ.get("AI_ANALYST_LOG_DIR", "logs")
LOG_LEVEL = os.environ.get("AI_ANALYST_LOG_LEVEL", "INFO")
LOG_RETENTION_DAYS = int(os.environ.get("AI_ANALYST_LOG_RETENTION_DAYS", "7"))
MAX_LOG_SIZE_MB = int(os.environ.get("AI_ANALYST_MAX_LOG_SIZE_MB", "50"))  # Max size per log file
BACKUP_COUNT = int(os.environ.get("AI_ANALYST_BACKUP_COUNT", "5"))  # Number of backup files to keep


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Set up a logger with consistent formatting and configuration.
    
    Args:
        name: Logger name (typically __name__ from the calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path(LOG_DIR)
    logs_dir.mkdir(exist_ok=True, parents=True)
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Set log level from parameter or environment
    log_level = getattr(logging, (level or LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Use date-based filenames with rotating handlers
    date_str = datetime.now().strftime('%Y%m%d')
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Rotating file handler for all logs (daily rotation with size limits)
    log_file = logs_dir / f"ai_analyst_{date_str}.log"
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,  # Convert MB to bytes
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Capture everything in file
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Rotating file handler for errors only
    error_log_file = logs_dir / f"ai_analyst_errors_{date_str}.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,  # Convert MB to bytes
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Log the file locations for debugging
    logger.info(f"Log files: {log_file} and {error_log_file}")
    logger.info(f"Max log size: {MAX_LOG_SIZE_MB}MB, Backup count: {BACKUP_COUNT}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance. Creates one if it doesn't exist.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(logger: logging.Logger):
    """Decorator to log function calls with arguments and execution time.
    
    Args:
        logger: Logger instance to use for logging
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.debug(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Completed {func.__name__} in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"Failed {func.__name__} after {execution_time:.3f}s: {e}")
                raise
                
        return wrapper
    return decorator


def log_query_execution(logger: logging.Logger, query: str, execution_time: float, row_count: int, error: str = None):
    """Log SQL query execution details.
    
    Args:
        logger: Logger instance
        query: SQL query that was executed
        execution_time: Time taken to execute query in seconds
        row_count: Number of rows returned
        error: Error message if query failed, None otherwise
    """
    if error:
        logger.error(f"Query failed ({execution_time:.3f}s): {query[:100]}... Error: {error}")
    else:
        logger.info(f"Query executed ({execution_time:.3f}s, {row_count} rows): {query[:100]}...")


def log_agent_activity(logger: logging.Logger, agent_name: str, activity: str, details: dict = None):
    """Log agent activity with structured information.
    
    Args:
        logger: Logger instance
        agent_name: Name of the agent (e.g., 'SQL Agent', 'Visualization Agent')
        activity: Activity being performed (e.g., 'Generating SQL', 'Creating chart')
        details: Additional details to log
    """
    message = f"{agent_name} - {activity}"
    if details:
        message += f" - {details}"
    logger.info(message)


# Configure root logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def cleanup_old_logs():
    """Clean up old log files based on retention period.
    
    Removes log files older than LOG_RETENTION_DAYS days.
    """
    try:
        logs_dir = Path(LOG_DIR)
        if not logs_dir.exists():
            return
        
        current_time = datetime.now()
        cutoff_time = current_time.timestamp() - (LOG_RETENTION_DAYS * 24 * 60 * 60)  # Convert days to seconds
        
        cleaned_count = 0
        for log_file in logs_dir.glob("ai_analyst_*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                cleaned_count += 1
                print(f"Removed old log file: {log_file}")
        
        if cleaned_count > 0:
            print(f"Cleaned up {cleaned_count} old log files")
            
    except Exception as e:
        print(f"Error cleaning up old logs: {e}")


def get_log_info():
    """Get current logging configuration and file locations.
    
    Returns:
        dict: Logging configuration information
    """
    return {
        "log_directory": LOG_DIR,
        "log_level": LOG_LEVEL,
        "retention_days": LOG_RETENTION_DAYS,
        "current_log_files": list(Path(LOG_DIR).glob("ai_analyst_*.log")) if Path(LOG_DIR).exists() else []
    }


# Auto-cleanup old logs on module import
cleanup_old_logs()
