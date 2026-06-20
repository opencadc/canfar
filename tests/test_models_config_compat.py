"""Characterization tests for the legacy auth-context compatibility mapping.

These pin the externally observable dict-like behavior of
``LegacyContextsMapping`` so a refactor onto ``collections.abc.Mapping``
preserves every contract callers rely on.
"""

from __future__ import annotations

import time
from collections.abc import Mapping

from pydantic import SecretStr

from canfar.models.active import ActiveConfig
from canfar.models.auth import OIDC, X509, OIDCCredential
from canfar.models.config import Configuration
from canfar.models.config_compat import LegacyContextsMapping
from canfar.models.http import Server
from tests.helpers.config import configuration_from_legacy_context


def _oidc_context(name: str = "TestOIDC") -> OIDC:
    """Build a valid legacy OIDC context with an embedded server."""
    return OIDC(
        server=Server(name=name, url="https://oidc.example.com", version="v1"),
        endpoints={
            "discovery": "https://oidc.example.com/.well-known/openid-configuration",
            "token": "https://oidc.example.com/token",
        },
        client={"identity": "test-client", "secret": "test-secret"},
        token={"access": "access-token", "refresh": "refresh-token"},
        expiry={"access": time.time() + 3600, "refresh": time.time() + 7200},
    )


def _config_with_oidc(name: str = "TestOIDC") -> Configuration:
    """Return a configuration carrying a single saved OIDC credential."""
    return configuration_from_legacy_context(name, _oidc_context(name))


def _config_with_credential_without_server(idp: str = "orphan") -> Configuration:
    """Return a configuration whose IDP has a credential but no server.

    The IDP is recorded in ``authentication`` yet no saved server matches it,
    so ``get_server_for_idp`` raises and the legacy context cannot be
    reconstructed. This reproduces the membership edge case where a saved
    authentication record has no resolvable science platform server.
    """
    credential = OIDCCredential(
        idp=idp,
        endpoints={
            "discovery": "https://oidc.example.com/.well-known/openid-configuration",
            "token": "https://oidc.example.com/token",
        },
        client={"identity": "test-client", "secret": "test-secret"},
        token={"access": "access-token", "refresh": "refresh-token"},
        expiry={"access": time.time() + 3600, "refresh": time.time() + 7200},
    )
    return Configuration(
        active=ActiveConfig(authentication=idp, server=None),
        authentication={idp: credential},
        servers={},
    )


class TestLegacyContextsMapping:
    """Pin the dict-like contract of the legacy contexts view."""

    def test_is_a_mapping(self) -> None:
        """The view satisfies the read-only Mapping protocol."""
        config = _config_with_oidc()
        assert isinstance(config.contexts, Mapping)

    def test_getitem_returns_legacy_context(self) -> None:
        """Indexing by IDP returns a reconstructed legacy context."""
        config = _config_with_oidc()
        idp = config.active.authentication

        context = config.contexts[idp]

        assert isinstance(context, OIDC)
        assert context.server is not None
        assert context.token is not None
        assert context.token.access is not None
        assert context.token.access.get_secret_value() == "access-token"

    def test_contains_true_and_false(self) -> None:
        """Membership reflects saved authentication IDP keys."""
        config = _config_with_oidc()
        idp = config.active.authentication

        assert idp in config.contexts
        assert "missing-idp" not in config.contexts

    def test_keys_match_saved_authentication(self) -> None:
        """``keys()`` returns exactly the saved authentication IDP keys."""
        config = _config_with_oidc()

        assert list(config.contexts.keys()) == list(config.authentication)

    def test_iter_yields_keys(self) -> None:
        """Iterating the mapping yields the IDP keys in key order."""
        config = _config_with_oidc()

        assert list(iter(config.contexts)) == list(config.authentication)

    def test_len_matches_saved_authentication(self) -> None:
        """``len()`` matches the number of saved authentication records."""
        config = _config_with_oidc()

        assert len(config.contexts) == len(config.authentication)

    def test_items_pairs_keys_and_contexts(self) -> None:
        """``items()`` yields ``(idp, context)`` pairs for every key."""
        config = _config_with_oidc()

        items = dict(config.contexts.items())

        assert list(items) == list(config.authentication)
        for key, context in items.items():
            assert isinstance(context, OIDC)
            assert context == config.contexts[key]

    def test_values_yield_contexts(self) -> None:
        """``values()`` yields the legacy contexts in key order."""
        config = _config_with_oidc()

        values = list(config.contexts.values())

        assert [type(v) for v in values] == [OIDC]
        assert values == [config.contexts[k] for k in config.authentication]

    def test_dict_roundtrip_via_mapping_protocol(self) -> None:
        """``dict(view)`` reconstructs the full key/context mapping."""
        config = _config_with_oidc()

        as_dict = dict(config.contexts)

        assert list(as_dict) == list(config.authentication)
        assert (
            as_dict[config.active.authentication]
            == (config.contexts[config.active.authentication])
        )

    def test_setitem_persists_context(self) -> None:
        """Assigning a context updates the underlying configuration.

        This is the mutation path used by the httpx auth refresh hooks
        (``client.config.contexts[idp] = context``) and must survive the
        switch to a read-only ``Mapping`` base.
        """
        config = _config_with_oidc()
        idp = config.active.authentication
        original = config.contexts[idp]

        updated = original.model_copy(
            update={
                "token": original.token.model_copy(
                    update={"access": SecretStr("rotated-access-token")}
                )
            }
        )
        config.contexts[idp] = updated

        roundtrip = config.contexts[idp]
        assert roundtrip.token is not None
        access = roundtrip.token.access
        assert access is not None
        recovered = (
            access.get_secret_value() if isinstance(access, SecretStr) else access
        )
        assert recovered == "rotated-access-token"


class TestCredentialWithoutServer:
    """Pin the contract for a saved credential whose IDP has no server.

    For such an IDP, ``__getitem__`` raises ``KeyError`` because the legacy
    context cannot be reconstructed without a server. These tests pin the
    two contracts that this edge case exposes:

    * ``__contains__`` is overridden to report direct membership in the
      saved authentication records, so ``idp in contexts`` stays ``True``
      exactly as on the pre-refactor class (an IDP can be a member even
      when its context is not currently resolvable).
    * ``.get()`` is supplied by the ``Mapping`` mixin and resolves through
      ``__getitem__``, so it returns its default for an unresolvable IDP
      rather than the value.
    """

    def test_orphan_idp_is_a_member(self) -> None:
        """An IDP with a credential but no server is still a member."""
        config = _config_with_credential_without_server()

        assert "orphan" in config.contexts

    def test_orphan_idp_not_a_member_when_absent(self) -> None:
        """Membership stays ``False`` for an IDP with no saved credential."""
        config = _config_with_credential_without_server()

        assert "definitely-missing" not in config.contexts

    def test_orphan_idp_getitem_raises_key_error(self) -> None:
        """Indexing an unresolvable IDP raises ``KeyError`` (no server)."""
        config = _config_with_credential_without_server()

        try:
            config.contexts["orphan"]
        except KeyError:
            pass
        else:  # pragma: no cover - failure path
            msg = "expected KeyError for credential-without-server IDP"
            raise AssertionError(msg)

    def test_orphan_idp_get_returns_default(self) -> None:
        """``.get()`` returns its default for an unresolvable IDP."""
        config = _config_with_credential_without_server()
        sentinel = object()

        assert config.contexts.get("orphan", sentinel) is sentinel

    def test_orphan_idp_is_counted_and_iterated(self) -> None:
        """The orphan IDP key participates in iteration and length."""
        config = _config_with_credential_without_server()

        assert "orphan" in list(config.contexts)
        assert len(config.contexts) == len(config.authentication)


def test_constructed_directly_over_configuration() -> None:
    """The mapping can be built directly over a configuration instance."""
    config = _config_with_oidc("DirectOIDC")
    mapping = LegacyContextsMapping(config)

    assert isinstance(mapping, Mapping)
    assert len(mapping) == 1
    (key,) = list(mapping)
    assert isinstance(mapping[key], (OIDC, X509))
