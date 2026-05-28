"""Legacy configuration detection and migration to config v1."""

from __future__ import annotations

import shutil
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path  # noqa: TC003
from typing import Any

import yaml

from canfar.models.config import (
    ConsoleConfig,
    default_active,
    default_authentication,
    default_servers,
)
from canfar.models.registry import ContainerRegistry

Clock = Callable[[], float]
"""Callable returning Unix timestamp seconds for backup naming."""


class ConfigMigrationError(Exception):
    """Raised when configuration migration cannot complete safely.

    Attributes:
        code: Stable dotted error code for automation.
        message: Human-readable error summary.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def is_legacy_config(data: dict[str, Any]) -> bool:
    """Return True when YAML data is not config v1.

    Args:
        data: Parsed configuration mapping.

    Returns:
        True if the config lacks version 1.
    """
    version = data.get("version")
    return version not in (1, "1")


def backup_path(config_path: Path, clock: Clock) -> Path:
    """Build a timestamped backup path for a config file.

    Args:
        config_path: Path to the live configuration file.
        clock: Injectable clock returning Unix epoch seconds.

    Returns:
        Backup path using ``<config-path>.<timestamp>.back`` naming.
    """
    instant = datetime.fromtimestamp(clock(), tz=timezone.utc)
    timestamp = instant.strftime("%Y%m%dT%H%M%SZ")
    return config_path.with_name(f"{config_path.name}.{timestamp}.back")


def _unique_backup_path(config_path: Path, clock: Clock) -> Path:
    candidate = backup_path(config_path, clock)
    if not candidate.exists():
        return candidate

    offset = 1
    while True:
        stamped = backup_path(config_path, clock)
        unique = stamped.with_name(f"{stamped.name}.{offset}")
        if not unique.exists():
            return unique
        offset += 1


def _preserve_sections(data: dict[str, Any]) -> dict[str, Any]:
    preserved: dict[str, Any] = {}
    if "registry" in data:
        preserved["registry"] = data["registry"]
    if "console" in data:
        preserved["console"] = data["console"]
    return preserved


def _default_v1_payload(preserved: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "version": 1,
        "active": default_active.model_dump(mode="json"),
        "authentication": [
            cred.model_dump(mode="json") for cred in default_authentication
        ],
        "server": [srv.model_dump(mode="json") for srv in default_servers],
        "registry": ContainerRegistry().model_dump(mode="json", exclude_none=True),
        "console": ConsoleConfig().model_dump(mode="json", exclude_none=True),
    }
    payload.update(preserved)
    return payload


def migrate_legacy_config(
    config_path: Path,
    *,
    clock: Clock | None = None,
) -> bool:
    """Migrate legacy configuration to v1 when needed.

    Legacy configs are backed up, then replaced with default v1 content
    while preserving ``registry`` and ``console`` sections.

    Args:
        config_path: Path to the YAML configuration file.
        clock: Injectable clock for backup timestamps.

    Returns:
        True if migration ran, False if the file was already v1 or absent.

    Raises:
        ConfigMigrationError: If backup fails; the original file is untouched.
    """
    if clock is None:
        clock = time.time

    if not config_path.exists():
        return False

    with config_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        msg = f"Configuration file {config_path} is not a mapping."
        code = "config.invalid"
        raise ConfigMigrationError(code, msg)

    if not is_legacy_config(data):
        return False

    destination = _unique_backup_path(config_path, clock)
    try:
        shutil.copy2(config_path, destination)
    except OSError as err:
        msg = f"Failed to back up configuration to {destination}: {err}"
        code = "config.invalid"
        raise ConfigMigrationError(code, msg) from err

    preserved = _preserve_sections(data)
    payload = _default_v1_payload(preserved)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        yaml.dump(payload, handle, default_flow_style=False, sort_keys=True, indent=2)

    return True


def ensure_v1_config(
    config_path: Path,
    *,
    clock: Clock | None = None,
) -> None:
    """Ensure configuration on disk is config v1.

    Args:
        config_path: Path to the YAML configuration file.
        clock: Injectable clock for backup timestamps.

    Raises:
        ConfigMigrationError: If migration cannot complete safely.
    """
    migrate_legacy_config(config_path, clock=clock)
