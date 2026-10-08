"""Configuration compatibility checks for the current schema."""

from __future__ import annotations

import reprlib
from typing import TYPE_CHECKING, Any

import yaml

from canfar.errors import ErrorCode

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from pydantic import ValidationError

_SECRET_SECTIONS = ("authentication", "registry")
"""Top-level sections whose values may hold credentials and are never printed."""


class ConfigResetRequiredError(Exception):
    """Raised when this client cannot read an existing configuration file.

    Attributes:
        code: Stable dotted error code for automation.
        message: ``CANFAR config error`` followed by one ``key = value`` line
            per problem.
        hint: Command that resets the file, then the next step.
    """

    def __init__(self, config_path: Path, problems: Iterable[str]) -> None:
        self.code = ErrorCode.CONFIG_INVALID.value
        self.message = "\n".join(
            ["CANFAR config error:", *(f"  {problem}" for problem in problems)]
        )
        self.hint = (
            "If you recently updated canfar, reset the configuration with "
            f"`rm {config_path}`, then run `canfar login` and try again."
        )
        super().__init__(self.message)

    @classmethod
    def from_validation(
        cls, config_path: Path, error: ValidationError
    ) -> ConfigResetRequiredError:
        """Describe each invalid configuration field as ``key = value (reason)``.

        Args:
            config_path: Path to the YAML configuration file.
            error: Validation error raised while loading ``Configuration``.

        Returns:
            Error listing every invalid field, with credential values hidden.
        """
        problems = []
        for item in error.errors():
            loc = item["loc"]
            key = ".".join(str(part) for part in loc)
            secret = bool(loc) and loc[0] in _SECRET_SECTIONS
            value = "<hidden>" if secret else reprlib.repr(item["input"])
            problems.append(f"{key} = {value} ({item['msg']})")
        return cls(config_path, problems)


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
        problem = f"invalid YAML: {' '.join(str(err).split())}"
        raise ConfigResetRequiredError(config_path, [problem]) from err

    if not isinstance(data, dict):
        problem = f"{reprlib.repr(data)} (expected a mapping of settings)"
        raise ConfigResetRequiredError(config_path, [problem])
    if data.get("version") not in (1, "1"):
        version = reprlib.repr(data["version"]) if "version" in data else "<missing>"
        problem = f"version = {version} (expected 1)"
        raise ConfigResetRequiredError(config_path, [problem])
