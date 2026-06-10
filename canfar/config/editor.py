"""Dotted-path editing helpers for configuration objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from canfar.models.config import Configuration


def _parse_dotted_path(path: str) -> list[str | int]:
    segments: list[str | int] = []
    for raw in path.split("."):
        if not raw:
            msg = f"Invalid path {path!r}: empty segment"
            raise ValueError(msg)
        segments.append(int(raw) if raw.isdigit() else raw)
    return segments


def _get_from_container(container: Any, key: str | int) -> Any:
    if isinstance(key, int):
        if not isinstance(container, list):
            msg = f"Expected list for index {key}"
            raise TypeError(msg)
        return container[key]

    if isinstance(container, dict):
        return container[key]

    msg = f"Expected mapping for key {key!r}"
    raise KeyError(msg)


def _set_in_container(container: Any, key: str | int, value: Any) -> None:
    if isinstance(key, int):
        if not isinstance(container, list):
            msg = f"Expected list for index {key}"
            raise TypeError(msg)
        container[key] = value
        return

    if isinstance(container, dict):
        container[key] = value
        return

    msg = f"Expected mapping for key {key!r}"
    raise TypeError(msg)


def _ensure_child_container(parent: Any, key: str | int) -> Any:
    if isinstance(key, int):
        msg = "List indices are not supported for intermediate path segments"
        raise TypeError(msg)

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
    if not segments:
        msg = "Path cannot be empty"
        raise ValueError(msg)

    data = config.model_dump(mode="python")
    cursor: Any = data

    for segment in segments[:-1]:
        cursor = _ensure_child_container(cursor, segment)

    _set_in_container(cursor, segments[-1], value)
    return config.__class__.model_validate(data)
