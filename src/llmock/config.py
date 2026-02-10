"""Configuration management - loads YAML with environment variable overrides."""

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

import yaml

# Type alias for the config dict
Config = dict[str, Any]

# Environment variable prefix for config overrides
ENV_PREFIX = "LLMOCK_"


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
        config = yaml.safe_load(f) or {}

    # Apply environment variable overrides
    _apply_env_overrides(config)
    return config


def _apply_env_overrides(
    config: Config, prefix: str = ENV_PREFIX, path: str = ""
) -> None:
    """Recursively traverse config dict and apply environment variable overrides.

    Environment variables use the format: LLMOCK_SECTION_KEY=value
    For lists, use semicolon-separated values: LLMOCK_CORS_ALLOW_ORIGINS=http://localhost:8000;http://localhost:5173

    Args:
        config: Configuration dict to modify in-place.
        prefix: Current environment variable prefix (includes parent keys).
        path: Current path in the config tree (for debugging).
    """
    for key, value in list(config.items()):
        # Build the environment variable name
        env_key = f"{prefix}{key.upper().replace('-', '_')}"

        # Check if env var exists
        env_value = os.getenv(env_key)

        if env_value is not None:
            # Apply the override
            if isinstance(value, list):
                # For lists, split by semicolon
                config[key] = env_value.split(";")
            elif isinstance(value, dict):
                # For dicts, can't override directly from env, but traverse it
                _apply_env_overrides(value, f"{env_key}_", f"{path}{key}.")
            else:
                # For scalars, use the value directly
                config[key] = env_value
        elif isinstance(value, dict):
            # Recursively process nested dicts
            _apply_env_overrides(value, f"{env_key}_", f"{path}{key}.")


@lru_cache
def get_config() -> Config:
    """Get cached configuration dict."""
    return load_config()
