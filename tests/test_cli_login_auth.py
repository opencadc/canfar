"""Tests for interactive CLI login credential acquisition."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import AnyHttpUrl

from canfar.cli.login_auth import authenticate_for_cli
from canfar.idp import IdpInfo, get_idp
from canfar.models.auth import OIDC, Client, Endpoint, Expiry, Token


def test_authenticate_for_cli_srcnet_uses_oidc_device_flow() -> None:
    """SRCNet login runs the interactive OIDC device authorization flow."""
    idp_info = get_idp("srcnet")
    updated = OIDC(
        endpoints=Endpoint(
            discovery="https://ska-iam.stfc.ac.uk/.well-known/openid-configuration",
            token="https://example.com/token",
        ),
        client=Client(identity="client-id", secret="client-secret"),
        token=Token(access="access-token", refresh="refresh-token"),
        expiry=Expiry(access=9999999999.0, refresh=9999999999.0),
    )

    with patch(
        "canfar.cli.login_auth.asyncio.run",
        return_value=updated,
    ) as mock_run:
        credential = authenticate_for_cli(idp_info)

    mock_run.assert_called_once()
    assert credential.idp == "srcnet"
    assert credential.mode == "oidc"
    assert credential.token.access == "access-token"


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
