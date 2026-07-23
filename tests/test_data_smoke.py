"""Optional authenticated smoke test for the configured CADC VOSpace Service."""

from __future__ import annotations

from typing import NoReturn

import pytest
from typer.testing import CliRunner

from canfar.auth import x509
from canfar.cli.main import cli
from canfar.models.config import Configuration


def _skip(reason: str) -> NoReturn:
    pytest.skip(
        "live data smoke requires Storage Name 'canfar' and a valid saved "
        f"Authentication Record/certificate: {reason}"
    )


def _require_live_credentials() -> None:
    """Skip unless persisted configuration can authenticate the live source."""
    try:
        config = Configuration()  # ty: ignore[missing-argument]
    except Exception:  # noqa: BLE001 - optional environment preflight.
        _skip("configuration is unavailable")

    try:
        _endpoint, idp = config._resolve_storage("canfar")  # noqa: SLF001
        credential = config.get_credential(idp)
    except (KeyError, ValueError):
        _skip("the named service or its Authentication Record is unavailable")

    if credential.mode == "x509":
        if credential.path is None:
            _skip("the saved X.509 certificate path is missing")
        try:
            x509.valid(credential.path)
            x509.expiry(credential.path)
        except (OSError, ValueError):
            _skip("the saved X.509 certificate is unavailable or invalid")
        return

    access = credential.token.access
    has_current_access = (
        access is not None
        and bool(access.get_secret_value())
        and not credential.expired
    )
    if not has_current_access and not credential.refreshable:
        _skip("the saved OIDC credential cannot authenticate or refresh")


@pytest.mark.integration
@pytest.mark.slow
def test_canfar_data_lists_live_primary_storage() -> None:
    """List the configured live CADC primary VOSpace Service when available."""
    _require_live_credentials()

    result = CliRunner().invoke(cli, ["data", "ls", "-lh", "canfar:/"])

    assert result.exit_code == 0, result.output
    assert not result.stdout.startswith("@")
