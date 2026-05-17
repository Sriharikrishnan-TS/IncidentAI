"""
Logging configuration for IncidentOS orchestration.

Provides structured, readable logging with:
- Consistent formatting
- Node identification
- Repository ID tracking
- Timestamp inclusion
- Multiple log levels
"""

import logging
import sys
from typing import Optional
from datetime import datetime


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

class OrchestrationFormatter(logging.Formatter):
    """
    Custom formatter for orchestration logs.
    
    Formats logs with:
    - Timestamp
    - Log level
    - Node name (if available)
    - Repository ID (if available)
    - Message
    """
    
    # Color codes for terminal output
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        """
        Initialize formatter.
        
        Args:
            use_colors: Whether to use colored output
        """
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string
        """
        # Get timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get level name
        level = record.levelname
        
        # Apply color if enabled
        if self.use_colors:
            color = self.COLORS.get(level, self.COLORS['RESET'])
            level_colored = f"{color}{level:8s}{self.COLORS['RESET']}"
        else:
            level_colored = f"{level:8s}"
        
        # Build log message
        parts = [
            timestamp,
            level_colored,
        ]
        
        # Add node name if available
        node_name = getattr(record, 'node_name', None)
        if node_name:
            parts.append(f"[{node_name}]")
        
        # Add repo ID if available
        repo_id = getattr(record, 'repo_id', None)
        if repo_id:
            parts.append(f"[repo_id={repo_id}]")
        
        # Add message
        parts.append(record.getMessage())
        
        # Join parts
        log_line = " ".join(parts)
        
        # Add exception info if present
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)
        
        return log_line


def configure_logging(
    level: str = "INFO",
    use_colors: bool = True,
    log_file: Optional[str] = None
) -> None:
    """
    Configure logging for orchestration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_colors: Whether to use colored output for console
        log_file: Optional file path for file logging
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(OrchestrationFormatter(use_colors=use_colors))
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(OrchestrationFormatter(use_colors=False))
        root_logger.addHandler(file_handler)


def get_logger(
    name: str,
    node_name: Optional[str] = None,
    repo_id: Optional[str] = None
) -> logging.LoggerAdapter:
    """
    Get a logger with optional context.
    
    Args:
        name: Logger name (usually __name__)
        node_name: Optional node name for context
        repo_id: Optional repository ID for context
        
    Returns:
        Logger adapter with context
    """
    logger = logging.getLogger(name)
    
    # Create context dict
    context = {}
    if node_name:
        context['node_name'] = node_name
    if repo_id:
        context['repo_id'] = repo_id
    
    # Return adapter with context
    return logging.LoggerAdapter(logger, context)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def log_node_start(logger: logging.Logger, node_name: str, repo_id: str) -> None:
    """
    Log node start with consistent format.
    
    Args:
        logger: Logger instance
        node_name: Name of the node
        repo_id: Repository ID
    """
    logger.info(
        f"Starting {node_name}",
        extra={'node_name': node_name, 'repo_id': repo_id}
    )


def log_node_complete(logger: logging.Logger, node_name: str, repo_id: str) -> None:
    """
    Log node completion with consistent format.
    
    Args:
        logger: Logger instance
        node_name: Name of the node
        repo_id: Repository ID
    """
    logger.info(
        f"Completed {node_name}",
        extra={'node_name': node_name, 'repo_id': repo_id}
    )


def log_callback_success(
    logger: logging.Logger,
    node_name: str,
    repo_id: str,
    endpoint: str
) -> None:
    """
    Log successful callback.
    
    Args:
        logger: Logger instance
        node_name: Name of the node
        repo_id: Repository ID
        endpoint: Callback endpoint
    """
    logger.info(
        f"Backend callback successful - {endpoint}",
        extra={'node_name': node_name, 'repo_id': repo_id}
    )


def log_callback_failure(
    logger: logging.Logger,
    node_name: str,
    repo_id: str,
    endpoint: str,
    error: str
) -> None:
    """
    Log callback failure.
    
    Args:
        logger: Logger instance
        node_name: Name of the node
        repo_id: Repository ID
        endpoint: Callback endpoint
        error: Error message
    """
    logger.warning(
        f"Backend callback failed - {endpoint}: {error}",
        extra={'node_name': node_name, 'repo_id': repo_id}
    )


def log_callback_skipped(
    logger: logging.Logger,
    node_name: str,
    repo_id: str
) -> None:
    """
    Log skipped callback.
    
    Args:
        logger: Logger instance
        node_name: Name of the node
        repo_id: Repository ID
    """
    logger.warning(
        "Backend callback skipped - not configured",
        extra={'node_name': node_name, 'repo_id': repo_id}
    )


# ============================================================================
# DEFAULT CONFIGURATION
# ============================================================================

# Configure logging on module import with sensible defaults
configure_logging(level="INFO", use_colors=True)

# Made with Bob
