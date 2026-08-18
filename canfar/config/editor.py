"""Dotted-path editing helpers for configuration objects."""

from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import ValidationError

from canfar.models.auth import OIDCCredential

if TYPE_CHECKING:
    from canfar.models.config import Configuration


def _parse_dotted_path(path: str) -> list[str]:
    segments: list[str] = []
    for raw in path.split("."):
        if not raw:
            msg = f"Invalid path {path!r}: empty segment"
            raise ValueError(msg)
        if raw.isdigit():
            msg = "List indices are not supported in configuration paths"
            raise ValueError(msg)
        segments.append(raw)
    return segments


def _get_from_container(container: Any, key: str) -> Any:
    if isinstance(container, dict):
        return container[key]

    msg = f"Expected mapping for key {key!r}"
    raise KeyError(msg)


def _set_in_container(container: Any, key: str, value: Any) -> None:
    if isinstance(container, dict):
        container[key] = value
        return

    msg = f"Expected mapping for key {key!r}"
    raise TypeError(msg)


def _ensure_child_container(parent: Any, key: str) -> Any:
    if not isinstance(parent, dict):
        msg = f"Expected mapping for key {key!r}"
        raise TypeError(msg)

    if key not in parent or parent[key] is None:
        parent[key] = {}
    return parent[key]


def get_value(config: Configuration, path: str) -> Any:
    """Get a nested configuration value via dotted path."""
    value: Any = config.model_dump(mode="json", exclude_none=False)
    for segment in _parse_dotted_path(path):
        value = _get_from_container(value, segment)
    return value


def _validated_copy(config: Configuration, **updates: Any) -> Configuration:
    """Validate a source-isolated copy of a complete Configuration."""
    data = {**config.model_dump(mode="python"), **updates}
    # Avoid BaseSettings merging the persisted YAML source into this copy.
    return config.__class__.model_validate(MappingProxyType(data))


def set_value(config: Configuration, path: str, value: Any) -> Configuration:
    """Return a new validated configuration with a dotted-path value updated."""
    segments = _parse_dotted_path(path)
    data = config.model_dump(mode="python")
    cursor: Any = data

    for segment in segments[:-1]:
        cursor = _ensure_child_container(cursor, segment)

    _set_in_container(cursor, segments[-1], value)
    return _validated_copy(config, **data)


def _restore_oidc_secrets(config: Configuration, data: dict[str, Any]) -> None:
    """Replace masked ``SecretStr`` placeholders with values for YAML persistence."""
    authentication = data.get("authentication")
    if not isinstance(authentication, dict):
        return

    for idp, credential_data in authentication.items():
        credential = config.authentication.get(idp)
        if not isinstance(credential, OIDCCredential) or not isinstance(
            credential_data, dict
        ):
            continue

        client = credential_data.get("client")
        if isinstance(client, dict) and credential.client.secret is not None:
            client["secret"] = credential.client.secret.get_secret_value()

        token = credential_data.get("token")
        if not isinstance(token, dict):
            continue
        if credential.token.access is not None:
            token["access"] = credential.token.access.get_secret_value()
        if credential.token.refresh is not None:
            token["refresh"] = credential.token.refresh.get_secret_value()


def _default_config_path() -> Path:
    """Resolve the configured YAML path lazily to preserve test isolation."""
    from canfar.models.config import CONFIG_PATH  # noqa: PLC0415

    return CONFIG_PATH


def _save_config(config: Configuration, path: Path | None = None) -> None:
    """Atomically save a validated Configuration to YAML."""
    target = path or _default_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        candidate = _validated_copy(config)
        data = candidate.model_dump(mode="json", exclude_none=True)
        _restore_oidc_secrets(candidate, data)
        serialized = yaml.dump(data, default_flow_style=False, sort_keys=True, indent=2)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(target)
    except (OSError, TypeError, ValidationError) as exc:
        if temporary is not None:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
        msg = f"Failed to save configuration to {target}: {exc}"
        raise OSError(msg) from exc


@dataclass(slots=True)
class ConfigurationEditor:
    """Bound editing and persistence boundary for a Configuration."""

    _config: Configuration

    def get(self, key: str) -> Any:
        """Read a scalar, mapping, or whole-list value by dotted path."""
        return get_value(self._config, key)

    def set(self, key: str, value: Any) -> Configuration:
        """Validate and install a dotted-path update on the bound config."""
        updated = set_value(self._config, key, value)
        self._config.__dict__.update(updated.__dict__)
        self._config.__pydantic_fields_set__ = updated.__pydantic_fields_set__.copy()
        return self._config

    def save(self) -> None:
        """Atomically persist the bound Configuration."""
        _save_config(self._config)
