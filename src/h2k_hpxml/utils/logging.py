"""
Logging configuration and utilities for H2K-HPXML translation.

This module provides standardized logging configuration for the entire application,
supporting both console and file output with configurable log levels.
"""

import logging
import logging.handlers
from pathlib import Path


class H2KLogger:
    """Centralized logging configuration for H2K-HPXML application."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            self._initialized = True

    def _setup_logging(self):
        """Setup logging configuration with console and file handlers."""
        # Get the root logger for our application
        self.logger = logging.getLogger("h2k_hpxml")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        simple_formatter = logging.Formatter("%(levelname)s - %(message)s")

        # Console handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)

        # Try to create log directory and file handler
        try:
            log_dir = Path.cwd() / "logs"
            log_dir.mkdir(exist_ok=True)

            # File handler (DEBUG and above) with rotation
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / "h2k_hpxml.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,  # 10MB
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)
        except (OSError, PermissionError):
            # If we can't create log files, continue with console only
            self.logger.warning("Could not create log file, using console output only")

    def get_logger(self, name=None):
        """Get a logger instance for a specific module or component.

        Args:
            name: Name for the logger, typically __name__ from calling module

        Returns:
            Logger instance configured with the application settings
        """
        if name:
            return logging.getLogger(f"h2k_hpxml.{name}")
        return self.logger

    def set_level(self, level):
        """Set the logging level for console output.

        Args:
            level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        if level.upper() in level_map:
            # Update console handler level
            for handler in self.logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(
                    handler, logging.FileHandler
                ):
                    handler.setLevel(level_map[level.upper()])
        else:
            self.logger.warning(f"Unknown logging level: {level}")


def get_logger(name=None):
    """Convenience function to get a logger instance.

    Args:
        name: Name for the logger, typically __name__ from calling module

    Returns:
        Logger instance configured with the application settings
    """
    h2k_logger = H2KLogger()
    return h2k_logger.get_logger(name)


def set_log_level(level):
    """Convenience function to set the logging level.

    Args:
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    h2k_logger = H2KLogger()
    h2k_logger.set_level(level)


def configure_from_config(config_dict):
    """Configure logging from configuration dictionary.

    Args:
        config_dict: Configuration dictionary with logging settings
    """
    log_level = config_dict.get("log_level", "INFO")
    set_log_level(log_level)

    logger = get_logger("config")
    logger.debug(f"Logging configured with level: {log_level}")
