"""
Logging configuration using loguru.
"""
import sys
from pathlib import Path
from loguru import logger

# Remove default handler
logger.remove()

# Create logs directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Add console handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Add file handler for all logs
logger.add(
    log_dir / "realestate_scraper_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# Add file handler for errors only
logger.add(
    log_dir / "errors_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="90 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

__all__ = ["logger"]
