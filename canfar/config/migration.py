"""Configuration compatibility checks for the current schema."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

from canfar.errors import ErrorCode

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


_RETIRED_SERVER_FIELDS = ("cores", "ram", "gpus", "status")
"""Server fields retired after v1.4.1; ``resources`` replaces the limits."""


def drop_retired_server_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Remove retired Server fields so v1.4.1 configuration files still load.

    The next save writes the configuration without them.

    Args:
        data: Parsed YAML configuration, changed in place.

    Returns:
        The same configuration data.
    """
    servers = data.get("servers")
    if isinstance(servers, dict):
        for server in servers.values():
            if isinstance(server, dict):
                for field in _RETIRED_SERVER_FIELDS:
                    server.pop(field, None)
    return data


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

    if not isinstance(data, dict) or data.get("version") not in (1, "1"):
        message = (
            "CANFAR configuration reset needed. "
            f"Run `rm -rf {config_path}` and perform a new login"
        )
        raise ConfigResetRequiredError(ErrorCode.CONFIG_INVALID.value, message)
