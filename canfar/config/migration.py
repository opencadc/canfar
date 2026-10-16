"""Configuration schema upgrades and the reset-required error."""

from __future__ import annotations

import reprlib
from typing import TYPE_CHECKING, Any

from canfar.errors import ErrorCode

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
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


def _v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    """Drop the v1.4.1 Server limits and console file; ``resources`` replaces them."""
    servers = data.get("servers")
    if isinstance(servers, dict):
        for server in servers.values():
            if isinstance(server, dict):
                for field in ("cores", "ram", "gpus", "status"):
                    server.pop(field, None)
    console = data.get("console")
    if isinstance(console, dict):
        console.pop("file", None)
    return data


UPGRADES: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {1: _v1_to_v2}
"""Steps keyed by the schema version they read; each returns the next version."""


def schema_version(config_path: Path, data: Any, current: int) -> int:
    """Return the version of a written document that this client can load.

    Args:
        config_path: Path to the YAML configuration file.
        data: Parsed YAML document.
        current: Schema version of ``Configuration``.

    Returns:
        ``current`` or an older version with an upgrade path to it.

    Raises:
        ConfigResetRequiredError: If the document is not a mapping or its
            version cannot be upgraded to ``current``.
    """
    if not isinstance(data, dict):
        problem = f"{reprlib.repr(data)} (expected a mapping of settings)"
        raise ConfigResetRequiredError(config_path, [problem])
    version = data.get("version")
    if isinstance(version, str) and version.isdecimal():
        version = int(version)
    if version == current or version in UPGRADES:
        return version
    shown = reprlib.repr(data["version"]) if "version" in data else "<missing>"
    problem = f"version = {shown} (expected {current})"
    raise ConfigResetRequiredError(config_path, [problem])


def upgrade(
    data: dict[str, Any], version: int, defaults: dict[str, Any]
) -> dict[str, Any]:
    """Step ``data`` up to the defaults' version, then fill omitted defaults.

    Args:
        data: Written document at ``version``, changed in place.
        version: Schema version of ``data``.
        defaults: Current default document, including its ``version``.

    Returns:
        Document at the current version. User values win; nested mappings merge.
    """
    data.pop("version", None)
    for step in range(version, defaults["version"]):
        data = UPGRADES[step](data)
    return _deep_merge(defaults, data)


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Overlay ``overlay`` onto ``base``.

    Nested mappings merge. Every other value replaces the base value.
    """
    merged = dict(base)
    for key, value in overlay.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(current, value)
        else:
            merged[key] = value
    return merged
