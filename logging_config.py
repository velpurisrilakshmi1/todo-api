"""
Logging configuration for Todo API
Provides structured logging with different levels and formatters
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict
import json
from datetime import datetime

from config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging() -> logging.Logger:
    """Setup logging configuration"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create main logger
    logger = logging.getLogger("todo_api")
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    if settings.debug:
        # Development: Colored, readable format
        console_formatter = ColoredFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Production: JSON format
        console_formatter = JSONFormatter()
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "todo_api.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "todo_api_errors.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)
    
    # Access log handler
    access_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "todo_api_access.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(JSONFormatter())
    
    # Create access logger
    access_logger = logging.getLogger("access")
    access_logger.setLevel(logging.INFO)
    access_logger.addHandler(access_handler)
    
    return logger


def get_logger(name: str = "todo_api") -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


def log_request(
    method: str,
    path: str,
    status_code: int,
    response_time: float,
    user_id: str = None,
    request_id: str = None
) -> None:
    """Log HTTP request details"""
    access_logger = logging.getLogger("access")
    
    extra = {
        'method': method,
        'endpoint': path,
        'status_code': status_code,
        'response_time': response_time
    }
    
    if user_id:
        extra['user_id'] = user_id
    if request_id:
        extra['request_id'] = request_id
        
    access_logger.info(
        f"{method} {path} - {status_code} - {response_time:.3f}s",
        extra=extra
    )


def log_error(
    error: Exception,
    context: Dict[str, Any] = None,
    user_id: str = None,
    request_id: str = None
) -> None:
    """Log error with context"""
    logger = get_logger()
    
    extra = {}
    if user_id:
        extra['user_id'] = user_id
    if request_id:
        extra['request_id'] = request_id
    if context:
        extra.update(context)
        
    logger.error(
        f"Error: {str(error)}",
        exc_info=True,
        extra=extra
    )


def log_security_event(
    event_type: str,
    details: Dict[str, Any],
    user_id: str = None,
    severity: str = "WARNING"
) -> None:
    """Log security-related events"""
    logger = get_logger()
    
    extra = {
        'event_type': 'SECURITY',
        'security_event': event_type,
        **details
    }
    
    if user_id:
        extra['user_id'] = user_id
        
    log_level = getattr(logger, severity.lower())
    log_level(
        f"Security Event: {event_type}",
        extra=extra
    )