"""CANFAR Authentication Configuration Module."""

from __future__ import annotations

import math
import time
from pathlib import Path  # noqa: TC003
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from canfar import get_logger
from canfar.auth import x509

log = get_logger(__name__)


def _secret_present(value: SecretStr | str | None) -> bool:
    """Return whether a secret field holds a non-empty value."""
    if value is None:
        return False
    if isinstance(value, SecretStr):
        return bool(value.get_secret_value())
    return bool(value)


AuthMode = Literal["x509", "oidc"]
"""Supported authentication modes for domain records."""


class Authentication(BaseModel):
    """CANFAR Authentication record."""

    model_config = ConfigDict(extra="forbid")

    idp: str = Field(description="Canonical Identity Provider key.")
    name: str = Field(description="Human-readable IDP name.")
    mode: AuthMode = Field(description="Authentication mode.")
    expiry: float | None = Field(
        default=None,
        description="Credential expiry as Unix timestamp when applicable.",
    )
    active: bool = Field(description="Whether this record is active.")
    server: str | None = Field(
        default=None,
        description="Selected server URI reference when available.",
    )


class Endpoint(BaseModel):
    """OIDC URL configuration."""

    discovery: Annotated[str | None, Field(description="OIDC discovery URL")] = None
    device: Annotated[
        str | None, Field(description="OIDC device authorization URL")
    ] = None
    registration: Annotated[
        str | None, Field(description="OIDC client registration URL")
    ] = None
    token: Annotated[str | None, Field(description="OIDC token endpoint URL")] = None


class Client(BaseModel):
    """OIDC client configuration."""

    identity: Annotated[str | None, Field(description="OIDC client ID")] = None
    secret: Annotated[
        SecretStr | None,
        Field(description="OIDC client secret"),
    ] = None


class Token(BaseModel):
    """OIDC token configuration."""

    access: Annotated[
        SecretStr | None,
        Field(description="Access token"),
    ] = None
    refresh: Annotated[
        SecretStr | None,
        Field(description="Refresh token"),
    ] = None
    token_type: Annotated[
        str | None,
        Field(description="OAuth token type"),
    ] = None
    scope: Annotated[
        str | None,
        Field(description="OAuth scope string"),
    ] = None


def _oidc_valid(endpoints: Endpoint, client: Client, token: Token) -> bool:
    """Return whether OIDC state can authenticate and refresh."""
    if not (
        endpoints.discovery
        and endpoints.token
        and client.identity
        and _secret_present(client.secret)
        and _secret_present(token.refresh)
    ):
        log.warning("Missing required OIDC configuration.")
        return False
    return True


class Expiry(BaseModel):
    """OIDC token expiry times."""

    access: Annotated[
        float | None, Field(description="Access token expiry in ctime")
    ] = None
    refresh: Annotated[
        float | None, Field(description="Refresh token expiry in ctime")
    ] = None


def _oidc_expired(expiry: Expiry) -> bool:
    """Return whether an OIDC access token is expired."""
    if expiry.access is None:
        log.warning("OIDC access token expiry is not set.")
        return True
    return expiry.access <= time.time()


def _x509_expiry(path: Path | None, expiry: float) -> float | None:
    """Return the known or certificate-derived X.509 expiry timestamp."""
    if path is None:
        return None
    if math.isclose(expiry, 0.0, abs_tol=1e-9):
        expiry = x509.expiry(path)
        log.debug("computed expiry from cert: %s", expiry)
    return expiry


class DeviceAuthorization(BaseModel):
    """OIDC device authorization challenge returned for user approval."""

    verification_uri: Annotated[
        str,
        Field(description="Provider URL where the user enters their code."),
    ]
    verification_uri_complete: Annotated[
        str | None,
        Field(
            default=None,
            description="Optional provider URL containing the user verification code.",
        ),
    ] = None
    user_code: Annotated[
        SecretStr,
        Field(description="Short-lived code displayed to the user."),
    ]
    expires_in: Annotated[
        int,
        Field(description="Challenge lifetime in seconds."),
    ]
    interval: Annotated[
        int,
        Field(default=5, description="Initial token polling interval in seconds."),
    ]
    device_code: Annotated[
        SecretStr,
        Field(description="Secret device code sent to the token endpoint."),
    ]


class X509Credential(BaseModel):
    """X.509 authentication credential decoupled from server selection."""

    idp: Annotated[str, Field(description="Canonical identity provider key.")]
    mode: Literal["x509"] = "x509"
    path: Annotated[
        Path | None,
        Field(
            title="x509 Certificate",
            description="Pathlike to PEM certificate",
        ),
    ] = None
    expiry: Annotated[
        float,
        Field(
            default=0.0,
            title="x509 Expiry Time",
            description="ctime of cert expiration",
        ),
    ]

    @property
    def expired(self) -> bool:
        """Return whether this X.509 Authentication Record is expired."""
        expiry = _x509_expiry(self.path, self.expiry)
        if expiry is None:
            return True
        self.expiry = expiry
        return expiry <= time.time()


class OIDCCredential(BaseModel):
    """OIDC authentication credential decoupled from server selection."""

    idp: Annotated[str, Field(description="Canonical identity provider key.")]
    mode: Literal["oidc"] = "oidc"
    endpoints: Annotated[
        Endpoint,
        Field(default_factory=Endpoint, description="OIDC Endpoints."),
    ]
    client: Annotated[
        Client,
        Field(default_factory=Client, description="OIDC Client Credentials."),
    ]
    token: Annotated[
        Token,
        Field(default_factory=Token, description="OIDC Tokens"),
    ]
    expiry: Annotated[
        Expiry,
        Field(default_factory=Expiry, description="OIDC Token Expiry."),
    ]

    @property
    def valid(self) -> bool:
        """Return whether this Authentication Record can refresh OIDC tokens."""
        return _oidc_valid(self.endpoints, self.client, self.token)

    @property
    def expired(self) -> bool:
        """Return whether this OIDC Authentication Record's access token expired."""
        return _oidc_expired(self.expiry)

    @property
    def refreshable(self) -> bool:
        """Return whether this record has usable, unexpired refresh credentials."""
        refresh_expiry = self.expiry.refresh
        return self.valid and (refresh_expiry is None or refresh_expiry > time.time())


AuthenticationCredential = Annotated[
    OIDCCredential | X509Credential, Field(discriminator="mode")
]
"""Discriminated union of v1 authentication credentials without embedded server."""

__all__ = [
    "AuthMode",
    "Authentication",
    "AuthenticationCredential",
    "Client",
    "DeviceAuthorization",
    "Endpoint",
    "Expiry",
    "OIDCCredential",
    "Token",
    "X509Credential",
]
