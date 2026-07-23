"""Interactive credential acquisition for CLI login flows."""

from __future__ import annotations

import asyncio
import webbrowser
from typing import TYPE_CHECKING, Any

import humanize
import segno
from rich import progress as rich_progress

from canfar.auth import oidc, x509
from canfar.models.auth import (
    AuthenticationCredential,
    Client,
    Endpoint,
    Expiry,
    OIDCCredential,
    Token,
    X509Credential,
)
from canfar.utils import console as console_utils

if TYPE_CHECKING:
    from authlib.integrations.httpx_client import AsyncOAuth2Client

    from canfar.idp import IdpInfo


async def _interactive_device_flow(
    device_auth_url: str,
    token_url: str,
    identity: str,
    secret: str,
    client: AsyncOAuth2Client,
) -> dict[str, Any]:
    """Present and complete one interactive OIDC device authorization."""
    challenge = await oidc.start_device_authorization(
        device_auth_url,
        identity,
        secret,
        client,
    )
    console = console_utils.get_console()
    console.print("[green]✓[/green] OIDC Configuration discovered successfully")
    console.print("[green]✓[/green] OIDC device registered successfully")
    console.print("[green]✓[/green] Follow the link below to authorize:")
    verification_url = challenge.verification_uri_complete or challenge.verification_uri
    console.print(f"\n  {verification_url}\n")
    console.print(f"[bold]Code:[/bold] {challenge.user_code.get_secret_value()}")

    qr = segno.make(verification_url, error="H")
    qr.terminal(compact=True)
    try:
        webbrowser.get().open(verification_url, new=2)
    except webbrowser.Error:
        console_utils.get_console(stderr=True).print(
            "[yellow]Failed to open browser. Please visit the URL manually.[/yellow]"
        )

    progress = rich_progress.Progress(
        rich_progress.TextColumn("[bold blue]{task.description}"),
        rich_progress.BarColumn(bar_width=None),
        rich_progress.TimeRemainingColumn(),
    )
    task_id = progress.add_task("Waiting for approval", total=challenge.expires_in)

    async def update_progress() -> None:
        for _ in range(challenge.expires_in):
            await asyncio.sleep(1)
            progress.update(task_id, advance=1)

    poll_task = asyncio.create_task(
        oidc.poll_device_token(token_url, challenge, client)
    )
    progress_task = asyncio.create_task(update_progress())
    try:
        with progress:
            try:
                tokens = await asyncio.wait_for(
                    poll_task,
                    timeout=challenge.expires_in + 5,
                )
            except asyncio.TimeoutError:
                msg = "Device flow timed out"
                raise TimeoutError(msg) from None
    finally:
        for task in (poll_task, progress_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(poll_task, progress_task, return_exceptions=True)

    console.print("[green]✓[/green] OIDC device authenticated successfully")
    return tokens


def authenticate_for_cli(
    idp_info: IdpInfo,
    *,
    timeout: int | None = None,
    force: bool = False,
) -> AuthenticationCredential:
    """Acquire Authentication credentials interactively for CLI login.

    Args:
        idp_info: Built-in Identity Provider metadata.
        timeout: HTTP timeout in seconds for OIDC requests.
        force: Obtain a new X.509 certificate instead of reusing an existing one.

    Returns:
        Saved-ready authentication credential without embedded server.

    Raises:
        ValueError: If credential acquisition fails.
        RuntimeError: If OIDC discovery URL is missing for an OIDC IDP.
    """
    if idp_info.auth_mode == "x509":
        return _authenticate_x509(idp_info.key, force=force)
    return _authenticate_oidc(idp_info, timeout=timeout)


def _authenticate_x509(idp: str, *, force: bool = False) -> X509Credential:
    """Reuse a valid X.509 certificate or acquire a replacement.

    Args:
        idp: Canonical Identity Provider key.
        force: Obtain a new certificate without inspecting the existing one.

    Returns:
        X509 credential record for persisted configuration.
    """
    if not force:
        try:
            info = x509.inspect()
        except x509.CertificateError as exc:
            if exc.expired_at is not None:
                age = humanize.naturaltime(exc.expired_at)
                console_utils.get_console().print(
                    f"[yellow]x509 certificate expired {age}[/yellow]"
                )
        except (FileNotFoundError, PermissionError, ValueError):
            pass
        else:
            return X509Credential(
                idp=idp,
                path=info["path"],
                expiry=float(info["expiry"] or 0.0),
            )

    return x509.authenticate_credential(X509Credential(idp=idp, expiry=0.0))


def _authenticate_oidc(
    idp_info: IdpInfo,
    *,
    timeout: int | None = None,
) -> OIDCCredential:
    """Run interactive OIDC device authorization for an IDP.

    Args:
        idp_info: Built-in Identity Provider metadata.
        timeout: HTTP timeout in seconds for OIDC requests.

    Returns:
        OIDC credential record for persisted configuration.

    Raises:
        RuntimeError: If the IDP has no configured OIDC discovery URL.
    """
    if idp_info.oidc_discovery_url is None:
        msg = f"OIDC discovery URL is not configured for IDP '{idp_info.key}'."
        raise RuntimeError(msg)
    if idp_info.oidc_issuer is None:
        msg = f"OIDC issuer is not configured for IDP '{idp_info.key}'."
        raise RuntimeError(msg)

    credential = OIDCCredential(
        idp=idp_info.key,
        endpoints=Endpoint(discovery=str(idp_info.oidc_discovery_url)),
        client=Client(),
        token=Token(),
        expiry=Expiry(),
    )
    console = console_utils.get_console()
    console.print("[bold blue]Starting OIDC Device Authentication[/bold blue]")
    return asyncio.run(
        oidc.authenticate_credential(
            credential,
            expected_issuer=str(idp_info.oidc_issuer),
            timeout=timeout,
            device_flow=_interactive_device_flow,
            on_authenticated=lambda username: console.print(
                f"[green]✓[/green] Successfully authenticated as {username}"
            ),
        )
    )
