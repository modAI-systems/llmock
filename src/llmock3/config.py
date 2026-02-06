"""Configuration management - loads YAML as a raw dict."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Type alias for the config dict
Config = dict[str, Any]


def load_config(config_path: Path = Path("config.yaml")) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Raw dict containing all config values.

    Raises:
        FileNotFoundError: If config file doesn't exist.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


@lru_cache
def get_config() -> Config:
    """Get cached configuration dict."""
    return load_config()
