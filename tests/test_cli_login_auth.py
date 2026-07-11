"""Tests for interactive CLI login credential acquisition."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from authlib.integrations.httpx_client import AsyncOAuth2Client
from pydantic import AnyHttpUrl

from canfar.cli.login_auth import authenticate_for_cli
from canfar.idp import IdpInfo, get_idp

_JWT = "eyJleHAiOjk5OTk5OTk5OTl9"


@pytest.mark.parametrize(
    ("complete_uri", "expected_uri"),
    [
        (
            "https://example.com/device?code=ABC123",
            "https://example.com/device?code=ABC123",
        ),
        (None, "https://example.com/device"),
    ],
)
def test_authenticate_for_cli_presents_oidc_device_challenge(
    complete_uri: str | None,
    expected_uri: str,
) -> None:
    """CLI login owns browser, QR, Rich, and human OIDC presentation."""
    idp_info = get_idp("srcnet")
    client = AsyncMock(spec=httpx.AsyncClient)
    oauth_client = AsyncMock(spec=AsyncOAuth2Client)
    discovery = MagicMock()
    discovery.json.return_value = {
        "issuer": "https://ska-iam.stfc.ac.uk/",
        "device_authorization_endpoint": "https://example.com/device",
        "registration_endpoint": "https://example.com/register",
        "token_endpoint": "https://example.com/token",
        "userinfo_endpoint": "https://example.com/userinfo",
    }
    registration = MagicMock()
    registration.json.return_value = {
        "client_id": "client-id",
        "client_secret": "client-secret",
    }
    device_authorization = MagicMock()
    device_authorization.json.return_value = {
        "verification_uri": "https://example.com/device",
        "verification_uri_complete": complete_uri,
        "user_code": "ABC123",
        "expires_in": 600,
        "interval": 5,
        "device_code": "device-code",
    }
    tokens = {
        "access_token": _JWT,
        "refresh_token": _JWT,
        "token_type": "Bearer",
        "scope": "openid profile email",
        "expires_at": 1893456000,
    }
    userinfo = MagicMock()
    userinfo.json.return_value = {"preferred_username": "test-user"}
    client.get.side_effect = [discovery, userinfo]
    client.post.return_value = registration
    oauth_client.post.return_value = device_authorization
    oauth_client.fetch_token = AsyncMock(return_value=tokens)
    console = MagicMock()

    with (
        patch("canfar.auth.oidc.httpx.AsyncClient") as client_class,
        patch(
            "authlib.integrations.httpx_client.AsyncOAuth2Client"
        ) as oauth_client_class,
        patch("canfar.utils.console.get_console", return_value=console),
        patch("webbrowser.get") as browser,
        patch("segno.make") as make_qr,
        patch("rich.progress.Progress") as progress,
    ):
        client_class.return_value.__aenter__.return_value = client
        oauth_client_class.return_value.__aenter__.return_value = oauth_client
        credential = authenticate_for_cli(idp_info, timeout=17)

    configured_timeout = client_class.call_args.kwargs["timeout"]
    assert configured_timeout.connect == 17
    assert configured_timeout.read == 17
    assert oauth_client_class.call_count == 1
    oauth_args = oauth_client_class.call_args
    assert oauth_args.args == ("client-id", "client-secret")
    assert oauth_args.kwargs["token_endpoint_auth_method"] == "client_secret_basic"
    assert oauth_args.kwargs["timeout"].connect == 17
    assert oauth_args.kwargs["timeout"].read == 17
    browser.return_value.open.assert_called_once_with(
        expected_uri,
        new=2,
    )
    make_qr.assert_called_once_with(
        expected_uri,
        error="H",
    )
    make_qr.return_value.terminal.assert_called_once_with(compact=True)
    assert progress.called
    console.print.assert_any_call(
        "[green]✓[/green] Successfully authenticated as test-user"
    )
    console.print.assert_any_call("[bold]Code:[/bold] ABC123")
    assert credential.idp == "srcnet"
    assert credential.token.access is not None
    assert credential.token.access.get_secret_value() == _JWT
    assert credential.token.refresh is not None
    assert credential.token.refresh.get_secret_value() == _JWT
    assert credential.token.token_type == "Bearer"
    assert credential.token.scope == "openid profile email"
    assert credential.expiry.access == 1893456000
    assert credential.expiry.refresh is None


def test_authenticate_for_cli_oidc_requires_discovery_url() -> None:
    """OIDC IDPs without discovery URLs fail fast."""
    idp_info = IdpInfo(
        key="srcnet",
        name="SKA Regional Centre Network",
        auth_mode="oidc",
        registry_url=AnyHttpUrl("https://spsrc27.iaa.csic.es/reg/resource-caps"),
        oidc_discovery_url=None,
    )

    with pytest.raises(RuntimeError, match="discovery URL"):
        authenticate_for_cli(idp_info)


def test_authenticate_for_cli_oidc_requires_expected_issuer() -> None:
    """OIDC IDPs without an expected issuer fail before network access."""
    idp_info = IdpInfo(
        key="srcnet",
        name="SKA Regional Centre Network",
        auth_mode="oidc",
        registry_url=AnyHttpUrl("https://spsrc27.iaa.csic.es/reg/resource-caps"),
        oidc_discovery_url=AnyHttpUrl(
            "https://ska-iam.stfc.ac.uk/.well-known/openid-configuration"
        ),
        oidc_issuer=None,
    )

    with pytest.raises(RuntimeError, match="issuer"):
        authenticate_for_cli(idp_info)
