"""Persistence helpers for configuration objects."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from pydantic import ValidationError

if TYPE_CHECKING:
    from pathlib import Path

    from canfar.models.config import Configuration


def _default_config_path() -> Path:
    from canfar.models.config import CONFIG_PATH  # noqa: PLC0415

    return CONFIG_PATH


def save_config(config: Configuration, path: Path | None = None) -> None:
    """Save ``config`` to YAML."""
    target = path or _default_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = config.model_dump(mode="json", exclude_none=True)
        with target.open(mode="w", encoding="utf-8") as handle:
            yaml.dump(data, handle, default_flow_style=False, sort_keys=True, indent=2)
    except (OSError, TypeError, ValidationError) as exc:
        msg = f"Failed to save configuration to {target}: {exc}"
        raise OSError(msg) from exc
