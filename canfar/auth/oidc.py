"""OIDC Device Authorization Flow."""

from __future__ import annotations

import asyncio
import contextlib
import math
import socket
import time
import webbrowser
from typing import Any

import httpx
import segno
from pydantic import SecretStr
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

from canfar import get_logger
from canfar.models.auth import OIDC
from canfar.utils import jwt

console = Console()
log = get_logger(__name__)


class AuthPendingError(Exception):
    """Exception raised when authorization is still pending."""


class SlowDownError(Exception):
    """Exception raised when the client should slow down its requests."""


async def discover(url: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    """Discover OIDC provider configuration.

    Args:
        url (str): OIDC Discovery URL.
        client (httpx.AsyncClient | None, optional): Optional async HTTP client.
            If None, creates a new one. Defaults to None.

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
    data: dict[str, Any] = resp.json()
    log.debug("OIDC Token Response: %s", data)
    if resp.status_code == 200:
        return data
    err = data.get("error")
    if err == "authorization_pending":
        raise AuthPendingError
    if err == "slow_down":
        raise SlowDownError
    msg = f"Unknown error in polling for tokens: {err}"
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
    payload: dict[str, Any] = {
        "client_id": identity,
        "scope": "openid profile email offline_access",
    }

    if client is None:
        async with httpx.AsyncClient() as http_client:
            return await _authflow_impl(
                device_auth_url, token_url, identity, secret, payload, http_client
            )
    else:
        return await _authflow_impl(
            device_auth_url, token_url, identity, secret, payload, client
        )


async def _cancel_pending_tasks(pending: set[asyncio.Task[Any]]) -> None:
    """Cancel pending tasks gracefully.

    Args:
        pending (set[asyncio.Task[Any]]): Set of pending tasks to cancel.
    """
    for task in pending:
        task.cancel()

    # Wait for cancelled tasks to finish gracefully
    for task in pending:
        with contextlib.suppress(asyncio.CancelledError):
            await task


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
    count: int = 0
    start: float = time.time()

    while True:
        try:
            return await _poll_token(token_url, identity, secret, code, client)
        except AuthPendingError:
            await asyncio.sleep(interval)
        except SlowDownError:
            # bump the slow_count and recompute interval
            count += 1
            interval = max(
                interval,
                int(interval * (1 + math.log(count + 1))),
            )
            await asyncio.sleep(interval)
        # check timeout
        if time.time() - start > expires:
            msg = "Device flow timed out"
            raise TimeoutError(msg)


async def _authflow_impl(
    device_auth_url: str,
    token_url: str,
    identity: str,
    secret: str,
    payload: dict[str, Any],
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    """Implementation of the auth flow with an existing client.

    Args:
        device_auth_url (str): Device authorization endpoint.
        token_url (str): Token endpoint.
        identity (str): Client identity.
        secret (str): Client secret.
        payload (dict[str, Any]): Request payload for device authorization.
        client (httpx.AsyncClient): Async HTTP client.

    Returns:
        dict[str, Any]: OIDC tokens including access and refresh tokens.

    Raises:
        TimeoutError: When the device flow times out.
    """
    response = await client.post(device_auth_url, data=payload, auth=(identity, secret))
    response.raise_for_status()
    verification = response.json()
    log.debug("OIDC Device Authorization Response: %s", verification)

    # Verification Details
    uri: str = str(verification["verification_uri_complete"])
    expires: int = int(verification["expires_in"])
    interval: int = int(verification.get("interval", 5))
    code: str = str(verification["device_code"])

    console.print("[green]✓[/green] Follow the link below to authorize:")
    console.print(f"\n  {uri}\n")
    qr = segno.make(uri, error="H")
    qr.terminal(compact=True)

    try:
        webbrowser.get().open(uri, new=2)
    except webbrowser.Error:
        console.print("[yellow]Failed to open browser. Please visit the URL manually.")

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TimeRemainingColumn(),
    )
    task_id = progress.add_task("Waiting for approval", total=expires)

    async def poll_loop() -> dict[str, Any]:
        """Poll for tokens with exponential backoff."""
        return await _poll_with_backoff(
            token_url, identity, secret, code, client, interval, expires
        )

    async def progress_updater() -> None:
        """Update progress bar every second."""
        elapsed = 0
        while elapsed < expires:
            await asyncio.sleep(1)
            elapsed += 1
            progress.update(task_id, advance=1)

    # Run progress bar and polling concurrently
    with progress:
        try:
            # Create tasks for concurrent execution
            poll_task = asyncio.create_task(poll_loop())
            progress_task = asyncio.create_task(progress_updater())

            # Wait for the polling task to complete
            done, pending = await asyncio.wait(
                [poll_task, progress_task],
                return_when=asyncio.FIRST_COMPLETED,
                timeout=expires + 5,  # Add small buffer
            )

            # Cancel any remaining tasks
            await _cancel_pending_tasks(pending)

            # Check if polling completed successfully
            if poll_task in done:
                return await poll_task

            msg = "Device flow timed out"
            raise TimeoutError(msg) from None

        except asyncio.TimeoutError as exc:
            msg = "Device flow timed out"
            raise TimeoutError(msg) from exc


async def authenticate(oidc: OIDC) -> OIDC:
    """Authenticate using OIDC Device Authorization Flow.

    Args:
        oidc (OIDC): OIDC configuration.

    Returns:
        OIDC: Updated OIDC configuration with tokens.
    """
    console.print("[bold blue]Starting OIDC Device Authentication[/bold blue]")
    async with httpx.AsyncClient() as client:
        response: dict[str, Any] = await discover(str(oidc.endpoints.discovery), client)
        oidc.endpoints.device = response["device_authorization_endpoint"]
        oidc.endpoints.registration = response["registration_endpoint"]
        oidc.endpoints.token = response["token_endpoint"]

        log.debug("Discovered OIDC configuration:")
        log.debug("Device Registration Endpoint: %s", oidc.endpoints.registration)
        log.debug("Device Authorization Endpoint: %s", oidc.endpoints.device)
        log.debug("Token Endpoint: %s", oidc.endpoints.token)

        console.print("[green]✓[/green] OIDC Configuration discovered successfully")

        device: dict[str, Any] = await register(
            str(oidc.endpoints.registration), client
        )
        oidc.client.identity = device["client_id"]
        oidc.client.secret = device["client_secret"]

        console.print("[green]✓[/green] OIDC device registered successfully")

        tokens = await authflow(
            str(oidc.endpoints.device),
            str(oidc.endpoints.token),
            str(oidc.client.identity),
            str(oidc.client.secret),
            client,
        )

        oidc.token.access = tokens["access_token"]
        oidc.token.refresh = tokens["refresh_token"]
        oidc.expiry.refresh = jwt.expiry(str(oidc.token.refresh))
        oidc.expiry.access = jwt.expiry(str(oidc.token.access))

        console.print("[green]✓[/green] OIDC device authenticated successfully")

        url: str = response["userinfo_endpoint"]
        headers = {
            "Authorization": f"Bearer {oidc.token.access}",
        }
        user = await client.get(url, headers=headers)
        user.raise_for_status()
        username = user.json().get("preferred_username")

        console.print(f"[green]✓[/green] Successfully authenticated as {username}")
        return oidc


if __name__ == "__main__":
    oidc_config = OIDC()  # type: ignore [call-arg]
    oidc_config.endpoints.discovery = (
        "https://ska-iam.stfc.ac.uk/.well-known/openid-configuration"
    )
    asyncio.run(authenticate(oidc_config))
