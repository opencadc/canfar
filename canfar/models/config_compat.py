"""Compatibility between current config and legacy auth-context callers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from canfar.models.auth import (
    OIDC,
    X509,
    AuthContext,
    OIDCCredential,
    X509Credential,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from canfar.models.auth import AuthenticationCredential
    from canfar.models.config import Configuration
    from canfar.models.http import Server


def credential_to_legacy_context(
    credential: AuthenticationCredential,
    server: Server | None,
) -> AuthContext:
    """Combine a saved credential and server into a legacy auth context.

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
        server=server,  # ty: ignore[invalid-argument-type]
    )


def legacy_context_to_credential(
    context: AuthContext,
    idp: str,
) -> AuthenticationCredential:
    """Extract a saved credential from a legacy auth context.

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


class LegacyContextsMapping(Mapping[str, "AuthContext"]):
    """Dict-like view over authentication records keyed by IDP.

    Subclasses :class:`collections.abc.Mapping`, so only ``__getitem__``,
    ``__iter__``, and ``__len__`` are implemented here; the mixin derives
    ``keys``, ``items``, ``values``, and ``__eq__``.

    ``__contains__`` is overridden to report direct membership in the saved
    authentication records, preserving the pre-refactor semantics: an IDP is
    a member when it has a saved credential, even if its legacy context is not
    currently resolvable (e.g. no matching server). The ``Mapping`` mixin's
    default ``__contains__`` would instead probe ``__getitem__`` and report
    ``False`` for such an IDP.

    ``__setitem__`` is retained for public compatibility assignments, which the
    read-only base does not provide. ``.get()`` is inherited from the mixin and
    resolves through ``__getitem__``, so it returns its default for an IDP whose
    context cannot be reconstructed.
    """

    def __init__(self, configuration: Configuration) -> None:
        self._configuration = configuration

    def __contains__(self, key: object) -> bool:
        """Return whether ``key`` is a saved authentication IDP."""
        return key in self._configuration.authentication

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
        return iter(self._configuration.authentication)

    def __len__(self) -> int:
        """Return the number of saved authentication records."""
        return len(self._configuration.authentication)
