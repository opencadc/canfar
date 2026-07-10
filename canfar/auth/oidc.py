"""OIDC Device Authorization Flow."""

from __future__ import annotations

import asyncio
import socket
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from pydantic import SecretStr, ValidationError

from canfar import get_logger
from canfar.models.auth import OIDC, DeviceAuthorization
from canfar.utils import jwt

log = get_logger(__name__)

DeviceFlow = Callable[
    [str, str, str, str, httpx.AsyncClient],
    Awaitable[dict[str, Any]],
]


class AuthPendingError(Exception):
    """Exception raised when authorization is still pending."""


class SlowDownError(Exception):
    """Exception raised when the client should slow down its requests."""


async def discover(
    url: str,
    client: httpx.AsyncClient | None = None,
    *,
    expected_issuer: str,
) -> dict[str, Any]:
    """Discover OIDC provider configuration.

    Args:
        url (str): OIDC Discovery URL.
        client (httpx.AsyncClient | None, optional): Optional async HTTP client.
            If None, creates a new one. Defaults to None.
        expected_issuer: Exact issuer configured for the Identity Provider.

    Returns:
        dict[str, Any]: OIDC provider configuration.
    """
    if client is None:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
    else:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    if data.get("issuer") != expected_issuer:
        msg = "OIDC discovery issuer mismatch"
        raise ValueError(msg)

    required = {
        "device_authorization_endpoint",
        "registration_endpoint",
        "token_endpoint",
        "userinfo_endpoint",
    }
    missing = sorted(field for field in required if not data.get(field))
    if missing:
        msg = f"OIDC discovery missing required metadata: {', '.join(missing)}"
        raise ValueError(msg)

    log.debug("OIDC Discovery Data: %s", data)
    return data


async def register(url: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    """Register a new client with the OIDC provider.

    Args:
        url (str): OIDC Registration URL.
        client (httpx.AsyncClient | None, optional): Optional async HTTP client.
            If None, creates a new one. Defaults to None.

    Returns:
        dict[str, Any]: Client registration details.
    """
    hostname = socket.gethostname()
    date = time.strftime("%Y-%m-%d %H:%M", time.gmtime())
    payload: dict[str, Any] = {
        "client_name": f"Science Platform CLI @ {hostname} {date}",
        "grant_types": [
            "urn:ietf:params:oauth:grant-type:device_code",
            "refresh_token",
        ],
        "response_types": ["token"],
        "token_endpoint_auth_method": "client_secret_basic",
        "scope": "openid profile email offline_access",
    }

    if client is None:
        async with httpx.AsyncClient() as http:
            response = await http.post(url, json=payload)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
    else:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    log.debug("OIDC Client Registration Data: %s", data)
    return data


async def _poll_token(
    url: str, identity: str, secret: str, code: str, client: httpx.AsyncClient
) -> dict[str, Any]:
    """Poll for OIDC tokens.

    Args:
        url (str): Token endpoint URL.
        identity (str): Client ID.
        secret (str): Client secret.
        code (str): Device code.
        client (httpx.AsyncClient): Async HTTP client.

    Returns:
        dict[str, Any]: Token response data.

    Raises:
        AuthPendingError: When authorization is still pending.
        SlowDownError: When client should slow down requests.
        ValueError: For unknown errors.
    """
    resp = await client.post(
        url,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": code,
            "client_id": identity,
            "client_secret": secret,
        },
        auth=(identity, secret),
    )
    try:
        data = resp.json()
    except ValueError:
        msg = "OIDC device authorization failed: malformed token response"
        raise ValueError(msg) from None
    if not isinstance(data, dict):
        msg = "OIDC device authorization failed: malformed token response"
        raise ValueError(msg)  # noqa: TRY004 - protocol value, not caller type
    log.debug("OIDC Token Response: %s", data)
    if resp.status_code == 200:
        return data
    err = data.get("error")
    if err == "authorization_pending":
        raise AuthPendingError
    if err == "slow_down":
        raise SlowDownError
    if err == "access_denied":
        msg = "OIDC device authorization was denied"
        raise PermissionError(msg)
    if err == "expired_token":
        msg = "OIDC device authorization expired"
        raise TimeoutError(msg)
    if not isinstance(err, str) or not err:
        msg = "OIDC device authorization failed: malformed token response"
        raise ValueError(msg)
    msg = f"OIDC device authorization failed: {err}"
    raise ValueError(msg)


async def refresh(
    url: str,
    identity: str,
    secret: str,
    token: str,
) -> SecretStr:
    """Refresh OIDC access token using refresh token.

    Args:
        url (str): Token endpoint URL.
        identity (str): Client ID.
        secret (str): Client secret.
        token (str): Refresh token.

    Returns:
        pydantic.SecretStr: New access token.

    Raises:
        httpx.HTTPStatusError: For HTTP errors.
        KeyError: If refresh token is invalid or expired.
        Exception: For other errors.
    """
    payload: dict[str, Any] = {
        "grant_type": "refresh_token",
        "refresh_token": token,
        "client_id": identity,
        "client_secret": secret,
    }

    try:
        async with httpx.AsyncClient() as client:
            log.debug("Refreshing OIDC access token")
            response = await client.post(url, data=payload, auth=(identity, secret))
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            log.debug("refresh http request successful")
            access: SecretStr = SecretStr(data["access_token"])
            return access
    except httpx.HTTPStatusError as error:
        msg = "HTTP error while refreshing OIDC access token"
        log.exception(msg)
        raise ValueError(msg) from error
    except KeyError as error:
        msg = "server response does not contain access token"
        log.exception(msg)
        raise ValueError(msg) from error
    except Exception as error:
        msg = "Failed to refresh OIDC access token"
        log.exception(msg)
        raise ValueError(msg) from error


def sync_refresh(
    url: str,
    identity: str,
    secret: str,
    token: str,
) -> SecretStr:
    """Refresh OIDC access token using refresh token.

    Args:
        url (str): Token endpoint URL.
        identity (str): Client ID.
        secret (str): Client secret.
        token (str): Refresh token.

    Returns:
        pydantic.SecretStr: New access token.

    Raises:
        httpx.HTTPStatusError: For HTTP errors.
        KeyError: If refresh token is invalid or expired.
        Exception: For other errors.
    """
    payload: dict[str, Any] = {
        "grant_type": "refresh_token",
        "refresh_token": token,
        "client_id": identity,
        "client_secret": secret,
    }

    try:
        with httpx.Client() as client:
            log.debug("Refreshing OIDC access token")
            response = client.post(url, data=payload, auth=(identity, secret))
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            log.debug("refresh http request successful")
            access: SecretStr = SecretStr(data["access_token"])
            return access
    except httpx.HTTPStatusError as error:
        msg = "HTTP error while refreshing OIDC access token"
        log.exception(msg)
        raise ValueError(msg) from error
    except KeyError as error:
        msg = "server response does not contain access token"
        log.exception(msg)
        raise ValueError(msg) from error
    except Exception as error:
        msg = "Failed to refresh OIDC access token"
        log.exception(msg)
        raise ValueError(msg) from error


async def authflow(
    device_auth_url: str,
    token_url: str,
    identity: str,
    secret: str,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """OIDC Authorization Flow.

    Args:
        device_auth_url (str): Device authorization endpoint.
        token_url (str): Token endpoint.
        identity (str): Client identity.
        secret (str): Client secret.
        client (httpx.AsyncClient | None, optional): Optional async HTTP client.
            If None, creates a new one. Defaults to None.

    Returns:
        dict[str, Any]: OIDC tokens including access and refresh tokens.
    """
    if client is None:
        async with httpx.AsyncClient() as http_client:
            return await _authflow_impl(
                device_auth_url, token_url, identity, secret, http_client
            )
    else:
        return await _authflow_impl(
            device_auth_url,
            token_url,
            identity,
            secret,
            client,
        )


async def start_device_authorization(
    url: str,
    identity: str,
    secret: str,
    client: httpx.AsyncClient,
) -> DeviceAuthorization:
    """Request an OIDC device authorization challenge.

    Args:
        url: Device authorization endpoint.
        identity: Registered client ID.
        secret: Registered client secret.
        client: Async HTTP client.

    Returns:
        Typed challenge data suitable for a caller-owned presentation layer.
    """
    response = await client.post(
        url,
        data={
            "client_id": identity,
            "scope": "openid profile email offline_access",
        },
        auth=(identity, secret),
    )
    response.raise_for_status()
    try:
        challenge = DeviceAuthorization.model_validate(response.json())
    except ValidationError:
        msg = "Invalid OIDC device authorization response"
        raise ValueError(msg) from None
    log.debug("OIDC device authorization challenge received")
    return challenge


async def poll_device_token(
    token_url: str,
    identity: str,
    secret: str,
    challenge: DeviceAuthorization,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    """Poll for tokens for an OIDC device authorization challenge.

    Args:
        token_url: Token endpoint.
        identity: Registered client ID.
        secret: Registered client secret.
        challenge: Challenge returned by :func:`start_device_authorization`.
        client: Async HTTP client.

    Returns:
        OIDC token response data.
    """
    return await _poll_with_backoff(
        token_url,
        identity,
        secret,
        challenge.device_code.get_secret_value(),
        client,
        challenge.interval,
        challenge.expires_in,
    )


async def _poll_with_backoff(
    token_url: str,
    identity: str,
    secret: str,
    code: str,
    client: httpx.AsyncClient,
    initial_interval: int,
    expires: int,
) -> dict[str, Any]:
    """Poll for tokens with exponential backoff.

    Args:
        token_url (str): Token endpoint URL.
        identity (str): Client ID.
        secret (str): Client secret.
        code (str): Device code.
        client (httpx.AsyncClient): Async HTTP client.
        initial_interval (int): Initial polling interval in seconds.
        expires (int): Expiration time in seconds.

    Returns:
        dict[str, Any]: Token response data.

    Raises:
        TimeoutError: When the device flow times out.
    """
    interval = initial_interval
    deadline = time.monotonic() + expires

    while time.monotonic() < deadline:
        try:
            return await _poll_token(token_url, identity, secret, code, client)
        except AuthPendingError:
            pass
        except SlowDownError:
            interval += 5
        except httpx.TransportError:
            interval *= 2
        remaining = deadline - time.monotonic()
        if remaining > 0:
            await asyncio.sleep(min(interval, remaining))

    msg = "Device flow timed out"
    raise TimeoutError(msg)


async def _authflow_impl(
    device_auth_url: str,
    token_url: str,
    identity: str,
    secret: str,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    """Implementation of the auth flow with an existing client.

    Args:
        device_auth_url (str): Device authorization endpoint.
        token_url (str): Token endpoint.
        identity (str): Client identity.
        secret (str): Client secret.
        client (httpx.AsyncClient): Async HTTP client.

    Returns:
        dict[str, Any]: OIDC tokens including access and refresh tokens.

    Raises:
        TimeoutError: When the device flow times out.
    """
    challenge = await start_device_authorization(
        device_auth_url,
        identity,
        secret,
        client,
    )

    return await poll_device_token(
        token_url,
        identity,
        secret,
        challenge,
        client,
    )


async def authenticate(
    oidc: OIDC,
    *,
    expected_issuer: str,
    timeout: int | None = None,
    device_flow: DeviceFlow | None = None,
    on_authenticated: Callable[[str | None], None] | None = None,
) -> OIDC:
    """Authenticate using OIDC Device Authorization Flow.

    Args:
        oidc (OIDC): OIDC configuration.
        expected_issuer: Exact issuer configured for the Identity Provider.
        timeout: HTTP timeout in seconds for OIDC HTTP requests.
        device_flow: Device authorization coordinator. Defaults to the
            presentation-free protocol flow.
        on_authenticated: Optional observer for the authenticated username.

    Returns:
        OIDC: Updated OIDC configuration with tokens.
    """
    if timeout is None:
        client_context = httpx.AsyncClient()
    else:
        client_context = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

    async with client_context as client:
        response: dict[str, Any] = await discover(
            str(oidc.endpoints.discovery),
            client,
            expected_issuer=expected_issuer,
        )
        oidc.endpoints.device = response["device_authorization_endpoint"]
        oidc.endpoints.registration = response["registration_endpoint"]
        oidc.endpoints.token = response["token_endpoint"]

        log.debug("Discovered OIDC configuration:")
        log.debug("Device Registration Endpoint: %s", oidc.endpoints.registration)
        log.debug("Device Authorization Endpoint: %s", oidc.endpoints.device)
        log.debug("Token Endpoint: %s", oidc.endpoints.token)

        device: dict[str, Any] = await register(
            str(oidc.endpoints.registration), client
        )
        oidc.client.identity = device["client_id"]
        oidc.client.secret = SecretStr(device["client_secret"])

        authorize = device_flow or authflow
        tokens = await authorize(
            str(oidc.endpoints.device),
            str(oidc.endpoints.token),
            str(oidc.client.identity),
            oidc.client.secret.get_secret_value() if oidc.client.secret else "",
            client,
        )

        oidc.token.access = SecretStr(tokens["access_token"])
        oidc.token.refresh = SecretStr(tokens["refresh_token"])
        oidc.expiry.refresh = jwt.expiry(oidc.token.refresh.get_secret_value())
        oidc.expiry.access = jwt.expiry(oidc.token.access.get_secret_value())

        url: str = response["userinfo_endpoint"]
        headers = {
            "Authorization": (
                f"Bearer {oidc.token.access.get_secret_value()}"
                if oidc.token.access
                else ""
            ),
        }
        user = await client.get(url, headers=headers)
        user.raise_for_status()
        username = user.json().get("preferred_username")
        if on_authenticated is not None:
            on_authenticated(username)
        return oidc


if __name__ == "__main__":
    oidc_config = OIDC()  # ty: ignore[missing-argument]
    oidc_config.endpoints.discovery = (
        "https://ska-iam.stfc.ac.uk/.well-known/openid-configuration"
    )
    asyncio.run(
        authenticate(
            oidc_config,
            expected_issuer="https://ska-iam.stfc.ac.uk/",
        )
    )
