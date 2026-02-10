"""Tests for configuration management with environment variable overrides."""

from pathlib import Path

import pytest
import yaml

from llmock.config import (
    ENV_PREFIX,
    _apply_env_overrides,
    load_config,
)


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create a temporary config file for testing."""
    config_data = {
        "api-key": "default-key",
        "cors": {
            "allow-origins": ["http://localhost:8000"],
        },
        "models": [
            {"id": "gpt-4", "created": 1700000000, "owned_by": "openai"},
            {"id": "gpt-3.5-turbo", "created": 1600000000, "owned_by": "openai"},
        ],
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    return config_file


# Basic config loading tests


def test_load_config_reads_yaml_file(temp_config_file: Path) -> None:
    """Test that load_config reads YAML file correctly."""
    config = load_config(temp_config_file)

    assert config["api-key"] == "default-key"
    assert config["cors"]["allow-origins"] == ["http://localhost:8000"]
    assert len(config["models"]) == 2


def test_load_config_missing_file_raises_error() -> None:
    """Test that missing config file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config(Path("/nonexistent/path/config.yaml"))


def test_load_config_empty_file_returns_empty_dict(tmp_path: Path) -> None:
    """Test that empty YAML file returns empty dict."""
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("")

    config = load_config(empty_file)
    assert config == {}


# Environment variable override tests


def test_override_scalar_value(
    temp_config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test overriding a scalar config value via env var."""
    monkeypatch.setenv(f"{ENV_PREFIX}API_KEY", "env-override-key")

    config = load_config(temp_config_file)

    assert config["api-key"] == "env-override-key"


def test_override_list_value_with_semicolon_separated(
    temp_config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test overriding a list value with semicolon-separated env var."""
    origins = "http://localhost:3000;http://example.com;http://dev.local"
    monkeypatch.setenv(f"{ENV_PREFIX}CORS_ALLOW_ORIGINS", origins)

    config = load_config(temp_config_file)

    assert config["cors"]["allow-origins"] == [
        "http://localhost:3000",
        "http://example.com",
        "http://dev.local",
    ]


def test_override_nested_key(
    temp_config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test overriding a nested config key."""
    monkeypatch.setenv(f"{ENV_PREFIX}CORS_ALLOW_ORIGINS", "http://localhost:5173")

    config = load_config(temp_config_file)

    assert config["cors"]["allow-origins"] == ["http://localhost:5173"]


def test_override_with_dashes_in_key_name(
    temp_config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that dashes in key names are converted to underscores in env vars."""
    monkeypatch.setenv(f"{ENV_PREFIX}API_KEY", "new-api-key")

    config = load_config(temp_config_file)

    # The key in YAML still has dash, but value should be overridden
    assert config["api-key"] == "new-api-key"


def test_default_value_used_when_env_var_not_set(
    temp_config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that default YAML values are used when env var is not set."""
    # Make sure env var is not set
    monkeypatch.delenv(f"{ENV_PREFIX}API_KEY", raising=False)

    config = load_config(temp_config_file)

    assert config["api-key"] == "default-key"
    assert config["cors"]["allow-origins"] == ["http://localhost:8000"]


def test_multiple_overrides(
    temp_config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test multiple environment variable overrides at once."""
    monkeypatch.setenv(f"{ENV_PREFIX}API_KEY", "override-key")
    monkeypatch.setenv(f"{ENV_PREFIX}CORS_ALLOW_ORIGINS", "http://prod.example.com")

    config = load_config(temp_config_file)

    assert config["api-key"] == "override-key"
    assert config["cors"]["allow-origins"] == ["http://prod.example.com"]


def test_override_empty_string_value(
    temp_config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that empty string env var can override default."""
    monkeypatch.setenv(f"{ENV_PREFIX}API_KEY", "")

    config = load_config(temp_config_file)

    # Empty string should still override
    assert config["api-key"] == ""


def test_override_list_with_single_value(
    temp_config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test overriding a list with a single value (no semicolon)."""
    monkeypatch.setenv(f"{ENV_PREFIX}CORS_ALLOW_ORIGINS", "http://localhost:3000")

    config = load_config(temp_config_file)

    # Single value should still be in a list
    assert config["cors"]["allow-origins"] == ["http://localhost:3000"]


def test_override_list_with_empty_values(
    temp_config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that empty segments in semicolon list are preserved."""
    monkeypatch.setenv(
        f"{ENV_PREFIX}CORS_ALLOW_ORIGINS",
        "http://localhost:8000;;http://localhost:3000",
    )

    config = load_config(temp_config_file)

    # Empty string in the middle should be preserved as part of split
    assert config["cors"]["allow-origins"] == [
        "http://localhost:8000",
        "",
        "http://localhost:3000",
    ]


# Direct _apply_env_overrides function tests


def test_apply_env_overrides_modifies_dict_in_place(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that _apply_env_overrides modifies the dict in-place."""
    config = {"api-key": "original", "nested": {"value": "default"}}
    monkeypatch.setenv(f"{ENV_PREFIX}API_KEY", "modified")

    _apply_env_overrides(config)

    assert config["api-key"] == "modified"


def test_apply_env_overrides_with_custom_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _apply_env_overrides with a custom prefix."""
    config = {"key": "original"}
    monkeypatch.setenv("CUSTOM_KEY", "modified")

    _apply_env_overrides(config, prefix="CUSTOM_")

    assert config["key"] == "modified"


def test_deeply_nested_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test overriding deeply nested values."""
    config = {
        "level1": {
            "level2": {
                "level3": "original",
            }
        }
    }
    monkeypatch.setenv(f"{ENV_PREFIX}LEVEL1_LEVEL2_LEVEL3", "modified")

    _apply_env_overrides(config)

    assert config["level1"]["level2"]["level3"] == "modified"


def test_complex_nested_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test override in a complex nested structure."""
    config = {
        "service": {
            "database": {
                "host": "localhost",
                "port": "5432",
            },
            "cache": {
                "ttl": "3600",
            },
        }
    }
    monkeypatch.setenv(f"{ENV_PREFIX}SERVICE_DATABASE_HOST", "prod.db.com")
    monkeypatch.setenv(f"{ENV_PREFIX}SERVICE_CACHE_TTL", "7200")

    _apply_env_overrides(config)

    assert config["service"]["database"]["host"] == "prod.db.com"
    assert config["service"]["database"]["port"] == "5432"  # unchanged
    assert config["service"]["cache"]["ttl"] == "7200"


# Integration tests


def test_full_workflow_yaml_with_env_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test complete workflow: load YAML and apply env overrides."""
    config_data = {
        "api-key": "yaml-key",
        "cors": {
            "allow-origins": ["http://localhost:8000"],
        },
        "max-connections": "10",
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    monkeypatch.setenv(f"{ENV_PREFIX}API_KEY", "env-key")
    monkeypatch.setenv(f"{ENV_PREFIX}CORS_ALLOW_ORIGINS", "http://prod.com")
    monkeypatch.setenv(f"{ENV_PREFIX}MAX_CONNECTIONS", "50")

    config = load_config(config_file)

    assert config["api-key"] == "env-key"
    assert config["cors"]["allow-origins"] == ["http://prod.com"]
    assert config["max-connections"] == "50"
