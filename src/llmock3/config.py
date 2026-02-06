"""Configuration management with YAML support."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class ModelConfig(BaseModel):
    """Configuration for a single model."""

    id: str = Field(description="The model identifier")
    created: int = Field(
        default=1700000000, description="Unix timestamp when model was created"
    )
    owned_by: str = Field(
        default="llmock3", description="Organization that owns the model"
    )


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """Settings source that loads from a YAML file."""

    def get_field_value(
        self,
        field: Any,  # noqa: ARG002 - required by interface
        field_name: str,
    ) -> tuple[Any, str, bool]:
        """Get field value from YAML config."""
        yaml_data = self._load_yaml()
        field_value = yaml_data.get(field_name)
        return field_value, field_name, False

    def _load_yaml(self) -> dict[str, Any]:
        """Load YAML configuration file."""
        config_path = Path("config.yaml")

        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f) or {}
        return {}

    def __call__(self) -> dict[str, Any]:
        """Return all settings from YAML."""
        return self._load_yaml()


class Settings(BaseSettings):
    """Application settings with YAML and environment variable support.

    Settings are loaded in the following order (later sources override earlier):
    1. Default values
    2. YAML config file (config.yaml by default)
    3. Environment variables (prefixed with LLMOCK3_)
    """

    model_config = SettingsConfigDict(
        env_prefix="LLMOCK3_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    # Application settings
    app_name: str = Field(default="LLMock3", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")

    # Config file path (not loaded from YAML itself)
    config_path: Path = Field(
        default=Path("config.yaml"), description="Path to YAML config file"
    )

    # Models configuration
    models: list[ModelConfig] = Field(
        default_factory=lambda: [
            ModelConfig(id="gpt-4o", created=1715367049, owned_by="openai"),
            ModelConfig(id="gpt-4o-mini", created=1721172741, owned_by="openai"),
            ModelConfig(id="gpt-3.5-turbo", created=1677610602, owned_by="openai"),
        ],
        description="List of models to expose",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to include YAML config."""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
