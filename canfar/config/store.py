"""Persistence helpers for configuration objects."""

from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import ValidationError

from canfar.models.auth import OIDCCredential

if TYPE_CHECKING:
    from canfar.models.config import Configuration


def _default_config_path() -> Path:
    from canfar.models.config import CONFIG_PATH  # noqa: PLC0415

    return CONFIG_PATH


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


def save_config(config: Configuration, path: Path | None = None) -> None:
    """Save ``config`` to YAML."""
    target = path or _default_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        data = config.model_dump(mode="json", exclude_none=True)
        _restore_oidc_secrets(config, data)
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
