"""Contract tests for public synchronous and asynchronous OIDC login."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import canfar
from canfar.models.auth import (
    Client,
    DeviceAuthorization,
    Endpoint,
    Expiry,
    OIDCCredential,
    Token,
)

if TYPE_CHECKING:
    from pathlib import Path


def _patch_config(path: Path):
    return patch("canfar.models.config.CONFIG_PATH", path)


def _credential() -> OIDCCredential:
    """Return a saved-ready SRCNet Authentication Record."""
    return OIDCCredential(
        idp="srcnet",
        endpoints=Endpoint(
            discovery="https://example.com/.well-known/openid-configuration"
        ),
        client=Client(identity="client-id", secret="client-secret"),
        token=Token(
            access="access-token",
            refresh="refresh-token",
            token_type="Bearer",
            scope="openid profile",
        ),
        expiry=Expiry(access=1893456000, refresh=None),
    )


def _challenge() -> DeviceAuthorization:
    """Return the presentation data exposed by the device protocol."""
    return DeviceAuthorization(
        verification_uri="https://example.com/device",
        verification_uri_complete="https://example.com/device?user_code=ABC123",
        user_code="ABC123",
        expires_in=600,
        interval=5,
        device_code="secret-device-code",
    )


def test_login_runs_plain_sync_oidc_flow_and_persists_record(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The sync Python API presents a challenge without CLI presentation tools."""
    config_path = tmp_path / "config.yaml"
    coordinator = MagicMock()

    def authenticate(credential: OIDCCredential, **kwargs) -> OIDCCredential:
        """Expose the challenge through the API's plain terminal callback."""
        assert credential.idp == "srcnet"
        kwargs["on_challenge"](_challenge())
        coordinator(**kwargs)
        return _credential()

    with (
        _patch_config(config_path),
        patch(
            "canfar.authentication.oidc.sync_authenticate_credential",
            side_effect=authenticate,
        ) as authenticate_credential,
        patch("canfar.authentication.server_service.discover", return_value=[]),
    ):
        canfar.login("srcnet")

    output = capsys.readouterr().out
    assert "https://example.com/device" in output
    assert "ABC123" in output
    assert "secret-device-code" not in output
    authenticate_credential.assert_called_once()
    with _patch_config(config_path):
        saved = canfar.models.config.Configuration()
    credential = saved.get_credential("srcnet")
    assert isinstance(credential, OIDCCredential)
    assert credential.token.access is not None
    assert credential.token.access.get_secret_value() == "access-token"


@pytest.mark.asyncio
async def test_alogin_uses_native_async_flow_without_asyncio_run(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The async API awaits native protocol work inside an existing event loop."""
    config_path = tmp_path / "config.yaml"

    async def authenticate(credential: OIDCCredential, **kwargs) -> OIDCCredential:
        """Expose the challenge through the async terminal callback."""
        assert credential.idp == "srcnet"
        kwargs["on_challenge"](_challenge())
        await asyncio.sleep(0)
        return _credential()

    with (
        _patch_config(config_path),
        patch(
            "canfar.authentication.oidc.authenticate_credential",
            new=AsyncMock(side_effect=authenticate),
        ) as authenticate_credential,
        patch("canfar.authentication.server_service.discover", return_value=[]),
        patch(
            "asyncio.run", side_effect=AssertionError("library API used asyncio.run")
        ),
    ):
        await canfar.alogin("srcnet")

    output = capsys.readouterr().out
    assert "https://example.com/device" in output
    assert "ABC123" in output
    assert "secret-device-code" not in output
    authenticate_credential.assert_awaited_once()
    with _patch_config(config_path):
        saved = canfar.models.config.Configuration()
    credential = saved.get_credential("srcnet")
    assert isinstance(credential, OIDCCredential)
    assert credential.token.access is not None
    assert credential.token.access.get_secret_value() == "access-token"
