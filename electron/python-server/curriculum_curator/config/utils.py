"""Utility functions for configuration."""

import os

import structlog

from curriculum_curator.config.models import AppConfig

logger = structlog.get_logger()


def find_config_file(config_path: str = None) -> str:
    """Find the configuration file.

    Args:
        config_path: Path to the configuration file, or None to search in default locations.

    Returns:
        str: Path to the configuration file.

    Raises:
        FileNotFoundError: If no configuration file is found.
    """
    # Check if the config_path is explicitly given and exists
    if config_path and os.path.exists(config_path):
        return config_path

    # If config_path is given but doesn't exist, raise an error
    if config_path:
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    # Search in default locations
    candidates = [
        "config.yaml",  # Current directory
        "~/.curriculum_curator/config.yaml",  # User home directory
        "/etc/curriculum_curator/config.yaml",  # System-wide
    ]

    for candidate in candidates:
        path = os.path.expanduser(candidate)
        if os.path.exists(path):
            return path

    raise FileNotFoundError(f"Configuration file not found. Searched in: {', '.join(candidates)}")


def load_config(config_path: str = None) -> AppConfig:
    """Load configuration from a file.

    Args:
        config_path: Path to the configuration file, or None to search in default locations.

    Returns:
        AppConfig: The loaded configuration.

    Raises:
        FileNotFoundError: If no configuration file is found.
    """
    config_file = find_config_file(config_path)
    logger.info("loading_config", path=config_file)

    try:
        config = AppConfig.from_file(config_file)
        logger.info(
            "config_loaded",
            llm_providers=list(config.llm.providers.keys()),
            workflows=list(config.workflows.keys()),
        )
        return config
    except Exception as e:
        logger.exception("config_load_failed", error=str(e))
        raise
