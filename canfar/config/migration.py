"""Configuration compatibility checks for the current schema."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path


class ConfigResetRequiredError(Exception):
    """Raised when an existing configuration must be manually reset.

    Attributes:
        code: Stable dotted error code for automation.
        message: Human-readable error summary.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def requires_manual_reset(data: dict[str, Any]) -> bool:
    """Return True when YAML data cannot be loaded as current configuration."""
    version = data.get("version")
    return version not in (1, "1")


def _reset_message(config_path: Path) -> str:
    return (
        "CANFAR configuration reset needed. "
        f"Run `rm -rf {config_path}` and perform a new login"
    )


def ensure_current_config(config_path: Path) -> None:
    """Require existing config files to use the current schema.

    Args:
        config_path: Path to the YAML configuration file.

    Raises:
        ConfigResetRequiredError: If the file is malformed or unsupported.
    """
    if not config_path.exists():
        return

    with config_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        code = "config.invalid"
        raise ConfigResetRequiredError(code, _reset_message(config_path))

    if requires_manual_reset(data):
        code = "config.invalid"
        raise ConfigResetRequiredError(code, _reset_message(config_path))
