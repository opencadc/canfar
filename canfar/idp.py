"""Built-in Identity Provider catalog for CANFAR."""

from __future__ import annotations

from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

AuthMode = Literal["x509", "oidc"]
"""Supported authentication modes for built-in Identity Providers."""


class IdpInfo(BaseModel):
    """Metadata for a built-in Identity Provider.

    Attributes:
        key: Canonical IDP key used in config and CLI selectors.
        name: Human-readable IDP name for CLI prompts.
        auth_mode: Default authentication mode for the IDP.
        registry_url: IVOA registry resource-caps URL for server discovery.
        oidc_discovery_url: OIDC discovery URL when ``auth_mode`` is ``oidc``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str = Field(description="Canonical IDP key.")
    name: str = Field(description="Human-readable IDP name.")
    auth_mode: AuthMode = Field(description="Default authentication mode.")
    registry_url: AnyHttpUrl = Field(
        description="IVOA registry resource-caps URL for server discovery."
    )
    oidc_discovery_url: AnyHttpUrl | None = Field(
        default=None,
        description="OIDC discovery URL for interactive CLI login.",
    )


_BUILTIN_IDPS: dict[str, IdpInfo] = {
    "cadc": IdpInfo(
        key="cadc",
        name="Canadian Astronomy Data Centre",
        auth_mode="x509",
        registry_url=AnyHttpUrl(
            "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps"
        ),
    ),
    "srcnet": IdpInfo(
        key="srcnet",
        name="SKA Regional Centre Network",
        auth_mode="oidc",
        registry_url=AnyHttpUrl("https://spsrc27.iaa.csic.es/reg/resource-caps"),
        oidc_discovery_url=AnyHttpUrl(
            "https://ska-iam.stfc.ac.uk/.well-known/openid-configuration"
        ),
    ),
}


def list_idps() -> list[IdpInfo]:
    """Return all built-in Identity Providers.

    Returns:
        list[IdpInfo]: Metadata for each built-in IDP in catalog definition order.
    """
    return list(_BUILTIN_IDPS.values())


def get_idp(key: str) -> IdpInfo:
    """Return metadata for a built-in Identity Provider.

    Args:
        key: Canonical IDP key.

    Returns:
        IdpInfo: Metadata for the requested IDP.

    Raises:
        KeyError: If ``key`` is not a built-in IDP.
    """
    try:
        return _BUILTIN_IDPS[key]
    except KeyError as exc:
        message = f"Unknown IDP: {key}"
        raise KeyError(message) from exc


def is_valid_idp(key: str) -> bool:
    """Return whether ``key`` identifies a built-in Identity Provider.

    Args:
        key: Candidate canonical IDP key.

    Returns:
        bool: ``True`` when ``key`` is a built-in IDP, otherwise ``False``.
    """
    return key in _BUILTIN_IDPS
