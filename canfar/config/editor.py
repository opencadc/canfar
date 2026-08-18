"""Dotted-path editing helpers for configuration objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

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


def set_value(config: Configuration, path: str, value: Any) -> Configuration:
    """Return a new validated configuration with a dotted-path value updated."""
    segments = _parse_dotted_path(path)
    data = config.model_dump(mode="python")
    cursor: Any = data

    for segment in segments[:-1]:
        cursor = _ensure_child_container(cursor, segment)

    _set_in_container(cursor, segments[-1], value)
    return config._validated_copy(**data)  # noqa: SLF001


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
        from canfar.config.store import save_config  # noqa: PLC0415

        save_config(self._config)
