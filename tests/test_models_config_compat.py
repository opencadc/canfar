"""Characterization tests for the legacy auth-context compatibility mapping.

These pin the externally observable dict-like behavior of
``LegacyContextsMapping`` so a refactor onto ``collections.abc.Mapping``
preserves every contract callers rely on.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import TYPE_CHECKING

from pydantic import SecretStr

from canfar.models.auth import OIDC, X509
from canfar.models.config_compat import LegacyContextsMapping
from canfar.models.http import Server
from tests.helpers.config import configuration_from_legacy_context

if TYPE_CHECKING:
    from canfar.models.config import Configuration


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


def test_constructed_directly_over_configuration() -> None:
    """The mapping can be built directly over a configuration instance."""
    config = _config_with_oidc("DirectOIDC")
    mapping = LegacyContextsMapping(config)

    assert isinstance(mapping, Mapping)
    assert len(mapping) == 1
    (key,) = list(mapping)
    assert isinstance(mapping[key], (OIDC, X509))
