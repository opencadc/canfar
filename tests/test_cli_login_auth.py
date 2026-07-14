"""Tests for interactive CLI login credential acquisition."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from authlib.integrations.httpx_client import AsyncOAuth2Client
from pydantic import AnyHttpUrl, SecretStr

from canfar.cli.login_auth import _interactive_device_flow, authenticate_for_cli
from canfar.idp import IdpInfo, get_idp
from canfar.models.auth import DeviceAuthorization, OIDCCredential, X509Credential

_OPAQUE_ACCESS_TOKEN = "opaque-access-token"
_OPAQUE_REFRESH_TOKEN = "opaque-refresh-token"


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
        "access_token": _OPAQUE_ACCESS_TOKEN,
        "refresh_token": _OPAQUE_REFRESH_TOKEN,
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
    assert isinstance(credential, OIDCCredential)
    assert credential.idp == "srcnet"
    assert credential.token.access is not None
    assert credential.token.access.get_secret_value() == _OPAQUE_ACCESS_TOKEN
    assert credential.token.refresh is not None
    assert credential.token.refresh.get_secret_value() == _OPAQUE_REFRESH_TOKEN
    assert credential.token.token_type == "Bearer"
    assert credential.token.scope == "openid profile email"
    assert credential.expiry.access == 1893456000
    assert credential.expiry.refresh is None


def test_authenticate_for_cli_builds_x509_record_from_gather(tmp_path) -> None:
    """CLI X.509 acquisition maps gathered certificate data without legacy state."""
    certificate = tmp_path / "cadcproxy.pem"
    gathered = {"path": str(certificate), "expiry": 1893456000.0}

    with patch("canfar.auth.x509.gather", return_value=gathered) as gather:
        result = authenticate_for_cli(get_idp("cadc"))

    assert isinstance(result, X509Credential)
    assert result.idp == "cadc"
    assert result.path == certificate
    assert result.expiry == 1893456000.0
    gather.assert_called_once_with()


def test_authenticate_for_cli_normalizes_x509_gather_failure() -> None:
    """CLI X.509 acquisition keeps the established failure prefix."""
    with (
        patch(
            "canfar.auth.x509.gather",
            side_effect=RuntimeError("certificate service unavailable"),
        ),
        pytest.raises(
            ValueError,
            match=r"^Failed to authenticate with X509 certificate:",
        ),
    ):
        authenticate_for_cli(get_idp("cadc"))


def test_authenticate_for_cli_normalizes_malformed_x509_gather_result() -> None:
    """CLI X.509 acquisition maps malformed certificate data to ValueError."""
    with (
        patch("canfar.auth.x509.gather", return_value={"expiry": 1893456000.0}),
        pytest.raises(
            ValueError,
            match=r"^Failed to authenticate with X509 certificate:",
        ),
    ):
        authenticate_for_cli(get_idp("cadc"))


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


@pytest.mark.asyncio
async def test_interactive_device_flow_awaits_poll_not_progress() -> None:
    """Progress finishing first must not timeout while poll is still pending."""
    challenge = DeviceAuthorization(
        verification_uri="https://example.com/device",
        user_code=SecretStr("ABC123"),
        expires_in=1,
        interval=5,
        device_code=SecretStr("device-code"),
    )
    expected_tokens = {
        "access_token": _OPAQUE_ACCESS_TOKEN,
        "refresh_token": _OPAQUE_REFRESH_TOKEN,
    }
    poll_started = asyncio.Event()
    release_http = asyncio.Event()
    real_sleep = asyncio.sleep

    async def instant_progress_sleep(delay: float) -> None:
        if delay == 1:
            return
        await real_sleep(delay)

    async def slow_poll(*_args, **_kwargs):
        poll_started.set()
        await release_http.wait()
        return expected_tokens

    client = AsyncMock(spec=AsyncOAuth2Client)
    console = MagicMock()
    progress_instance = MagicMock()
    progress_instance.__enter__ = MagicMock(return_value=progress_instance)
    progress_instance.__exit__ = MagicMock(return_value=False)
    progress_instance.add_task = MagicMock(return_value=1)

    with (
        patch(
            "canfar.cli.login_auth.oidc.start_device_authorization",
            AsyncMock(return_value=challenge),
        ),
        patch(
            "canfar.cli.login_auth.oidc.poll_device_token",
            side_effect=slow_poll,
        ),
        patch("canfar.utils.console.get_console", return_value=console),
        patch("webbrowser.get"),
        patch("segno.make"),
        patch(
            "canfar.cli.login_auth.rich_progress.Progress",
            return_value=progress_instance,
        ),
        patch("asyncio.sleep", side_effect=instant_progress_sleep),
    ):
        flow_task = asyncio.create_task(
            _interactive_device_flow(
                "https://example.com/device",
                "https://example.com/token",
                "client-id",
                "client-secret",
                client,
            )
        )
        await poll_started.wait()
        for _ in range(10):
            await real_sleep(0)
            if flow_task.done():
                break
        release_http.set()
        tokens = await flow_task

    assert tokens == expected_tokens


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
