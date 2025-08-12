"""CANFAR Authentication Configuration Module."""

from __future__ import annotations

import math
import time
from pathlib import Path  # noqa: TC003
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from canfar import get_logger
from canfar.auth import x509
from canfar.models.http import Server

log = get_logger(__name__)


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
    secret: Annotated[str | None, Field(description="OIDC client secret")] = None


class Token(BaseModel):
    """OIDC token configuration."""

    access: Annotated[str | None, Field(description="Access token")] = None
    refresh: Annotated[str | None, Field(description="Refresh token")] = None


class Expiry(BaseModel):
    """OIDC token expiry times."""

    access: Annotated[
        float | None, Field(description="Access token expiry in ctime")
    ] = None
    refresh: Annotated[
        float | None, Field(description="Refresh token expiry in ctime")
    ] = None


class OIDC(BaseModel):
    """Complete OIDC configuration."""

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
    server: Annotated[
        Server,
        Field(default_factory=Server, description="Science Platform Server."),
    ]
    expiry: Annotated[
        Expiry,
        Field(default_factory=Expiry, description="OIDC Token Expiry."),
    ]

    @property
    def valid(self) -> bool:
        """Check if all required information for getting new access tokens exists.

        Returns:
            bool: True if all required OIDC information is present, False otherwise.
        """
        required: list[str | float | None] = [
            self.endpoints.discovery,
            self.endpoints.token,
            self.client.identity,
            self.client.secret,
            self.token.refresh,
        ]

        # Check if all required fields are defined
        if not all(required):
            log.warning("Missing required OIDC configuration.")
            return False

        return True

    @property
    def expired(self) -> bool:
        """Check if the OIDC access token is active.

        Returns:
            bool: True if the access token is active, False otherwise.
        """
        if self.expiry.access is None:
            log.warning("OIDC access token expiry is not set.")
            return True
        return self.expiry.access < time.time()


class X509(BaseModel):
    """X.509 certificate configuration."""

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
    server: Annotated[
        Server | None,
        Field(description="X509 server information"),
    ] = None

    @property
    def valid(self) -> bool:
        """Check if the certificate filepath is defined and expiry is in the future.

        Returns:
            bool: True if certificate path exists and is not expired, False otherwise.
        """
        if self.path is None:
            return False
        try:
            x509.valid(self.path)
        except (FileNotFoundError, ValueError) as err:
            msg = "Failed to validate x509 certificate: %s", err
            log.exception(msg)
            return False
        return True

    @property
    def expired(self) -> bool:
        """Check if the X.509 certificate is expired.

        Returns:
            bool: True if the certificate is expired, False otherwise.
        """
        if self.path is None:
            return True
        if math.isclose(self.expiry, 0.0, abs_tol=1e-9):
            self.expiry = x509.expiry(self.path)
            log.debug("computed expiry from cert: %s", self.expiry)
        return self.expiry < time.time()


class TokenAuth(BaseModel):
    """Token authentication configuration."""

    mode: Literal["token"] = "token"
    token: Annotated[
        str | None,
        Field(
            default=None,
            title="Authentication Token",
            description="Authentication token for the server.",
        ),
    ] = None
    server: Annotated[
        Server | None,
        Field(description="Token server information"),
    ] = None
