"""Transitional compatibility between config v1 and legacy auth-context callers."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

from canfar.models.auth import (
    OIDC,
    X509,
    OIDCCredential,
    X509Credential,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from canfar.models.auth import AuthenticationCredential
    from canfar.models.config import Configuration
    from canfar.models.http import Server

AuthContext: TypeAlias = OIDC | X509
"""Legacy authentication context shape with embedded server."""


def credential_to_legacy_context(
    credential: AuthenticationCredential,
    server: Server | None,
) -> AuthContext:
    """Combine a v1 credential and server into a legacy auth context.

    Args:
        credential: Saved authentication credential for an IDP.
        server: Science platform server paired with the credential.

    Returns:
        Legacy ``OIDC`` or ``X509`` model with embedded ``server``.
    """
    if credential.mode == "x509":
        return X509(
            path=credential.path,
            expiry=credential.expiry,
            server=server,
        )
    return OIDC(
        endpoints=credential.endpoints,
        client=credential.client,
        token=credential.token,
        expiry=credential.expiry,
        server=server,
    )


def legacy_context_to_credential(
    context: AuthContext,
    idp: str,
) -> AuthenticationCredential:
    """Extract a v1 credential from a legacy auth context.

    Args:
        context: Legacy authentication context.
        idp: Canonical IDP key for the credential record.

    Returns:
        Decoupled authentication credential without embedded server.
    """
    if isinstance(context, X509):
        return X509Credential(idp=idp, path=context.path, expiry=context.expiry)
    return OIDCCredential(
        idp=idp,
        endpoints=context.endpoints,
        client=context.client,
        token=context.token,
        expiry=context.expiry,
    )


class LegacyContextsMapping:
    """Dict-like view over v1 authentication records keyed by IDP."""

    def __init__(self, configuration: Configuration) -> None:
        self._configuration = configuration

    def __contains__(self, key: str) -> bool:
        """Return whether ``key`` is a saved authentication IDP."""
        return any(cred.idp == key for cred in self._configuration.authentication)

    def __getitem__(self, key: str) -> AuthContext:
        """Return the legacy auth context for ``key``."""
        credential = self._configuration.get_credential(key)
        server = self._configuration.get_server_for_idp(key)
        return credential_to_legacy_context(credential, server)

    def __setitem__(self, key: str, context: AuthContext) -> None:
        """Persist a legacy auth context for ``key``."""
        self._configuration.set_legacy_context(key, context)

    def __iter__(self) -> Iterator[str]:
        """Iterate saved authentication IDP keys."""
        return iter(self.keys())

    def keys(self) -> list[str]:
        """Return saved authentication IDP keys."""
        return [cred.idp for cred in self._configuration.authentication]

    def items(self) -> Iterator[tuple[str, AuthContext]]:
        """Yield ``(idp, legacy_context)`` pairs."""
        for key in self.keys():
            yield key, self[key]

    def values(self) -> Iterator[AuthContext]:
        """Yield legacy auth contexts in IDP key order."""
        for key in self.keys():
            yield self[key]

    def __len__(self) -> int:
        """Return the number of saved authentication records."""
        return len(self._configuration.authentication)
