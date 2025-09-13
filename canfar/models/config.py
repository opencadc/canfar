"""CANFAR Client Configuration - V2."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import yaml
from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    Field,
    ValidationError,
    model_validator,
)
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from canfar import CONFIG_PATH, get_logger
from canfar.models.auth import OIDC, X509
from canfar.models.http import Server
from canfar.models.registry import ContainerRegistry

log = get_logger(__name__)

AuthContext = Annotated[OIDC | X509, Field(discriminator="mode")]
"""A discriminated union of all supported authentication contexts."""

# Default authentication context
# This is value that will be used if no configuration file is found
default: dict[str, AuthContext] = {
    "default": X509(
        path=Path.home() / ".ssl" / "cadcproxy.pem",
        expiry=0.0,
        server=Server(
            name="CADC-CANFAR",
            uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
            version="v1",
            auths=["x509"],
        ),
    )
}


class Configuration(BaseSettings):
    """Unified configuration settings for CANFAR client and authentication.

    This model manages all persistent configurations for the canfar client,
    including multiple authentication contexts and container registry settings.
    It loads settings from a YAML file, environment variables, and finally,
    defaults defined in the models.

    The structure is designed to support multiple, named server contexts,
    allowing users to easily switch between them.
    """

    model_config = SettingsConfigDict(
        title="CANFAR Configuration",
        env_prefix="CANFAR_",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        json_schema_mode_override="serialization",
        str_strip_whitespace=True,
    )

    active: str = Field(
        default="default",
        title="Active Authentication Context",
        description="The name of the context to use for authentication.",
    )
    contexts: dict[str, AuthContext] = Field(
        default_factory=lambda: default,
        description="A key-value mapping of available authentication contexts.",
    )
    registry: ContainerRegistry = Field(
        default_factory=ContainerRegistry,
        description="Container Registry Settings.",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to automatically load from YAML config file.

        Args:
            settings_cls (type[BaseSettings]): The settings class being configured.
            init_settings (PydanticBaseSettingsSource): Settings from init arguments.
            env_settings (PydanticBaseSettingsSource): Settings from env variables.
            dotenv_settings (PydanticBaseSettingsSource): Settings from .env files.
            file_secret_settings (PydanticBaseSettingsSource): Settings from secrets.

        Note: The order of sources determines priority, with earlier sources taking
        precedence.

        Returns:
            tuple[PydanticBaseSettingsSource, ...]: A tuple of settings sources.
        """
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=CONFIG_PATH),
            file_secret_settings,
        )

    @model_validator(mode="after")
    def _validate_contexts(self) -> Configuration:
        """Validate the integrity of the authentication contexts.

        Note: This validation does not check the validity of the credentials
        within each context, only the integrity of the context structure.

        Raises:
            ValueError: If the configuration is invalid.

        Returns:
            Configuration: The validated configuration.
        """
        if self.active not in self.contexts:
            msg = f"Active context '{self.active}' not found in available contexts."
            raise ValueError(msg)
        return self

    def save(self) -> None:
        """Save the current configuration to the default YAML file."""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Use `model_dump` which is the Pydantic v2 equivalent of `dict`
            data = self.model_dump(mode="json", exclude_none=True)
            with CONFIG_PATH.open(mode="w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=True, indent=2)
        except (OSError, TypeError, ValidationError) as e:
            msg = f"Failed to save configuration to {CONFIG_PATH}: {e}"
            raise OSError(msg) from e

    @property
    def context(self) -> AuthContext:
        """Get the active authentication context.

        Returns:
            AuthContext: The active authentication context.
        """
        return self.contexts[self.active]
