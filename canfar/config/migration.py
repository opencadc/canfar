"""Configuration compatibility checks for the current schema."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

from canfar.errors import ErrorCode

if TYPE_CHECKING:
    from pathlib import Path


class ConfigResetRequiredError(Exception):
    """Raised when this client cannot read an existing configuration file.

    Attributes:
        code: Stable dotted error code for automation.
        message: Human-readable error summary.
        hint: Command that moves the file aside, then the next step.
    """

    def __init__(self, config_path: Path) -> None:
        self.code = ErrorCode.CONFIG_INVALID.value
        self.message = (
            f"canfar configuration file has changed: {config_path} "
            "cannot be read by this version."
        )
        self.hint = (
            f"Run `mv -i {config_path} {config_path.with_suffix('.bak')}`, "
            "then `canfar login` and try again."
        )
        super().__init__(self.message)


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

    try:
        with config_path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except yaml.YAMLError as err:
        raise ConfigResetRequiredError(config_path) from err

    if not isinstance(data, dict) or data.get("version") not in (1, "1"):
        raise ConfigResetRequiredError(config_path)
