"""Behavior tests for the built-in Identity Provider catalog."""

from __future__ import annotations

import pytest

from canfar.idp import IdpInfo, get_idp, is_valid_idp, list_idps


class TestListIdps:
    """Tests for list_idps()."""

    def test_list_idps_returns_builtin_entries(self) -> None:
        """Built-in catalog includes canonical cadc and srcnet keys."""
        keys = {idp.key for idp in list_idps()}

        assert keys == {"cadc", "srcnet"}

    def test_list_idps_returns_idp_info_instances(self) -> None:
        """Each catalog entry is an IdpInfo model."""
        idps = list_idps()

        assert len(idps) == 2
        assert all(isinstance(idp, IdpInfo) for idp in idps)


class TestGetIdpCadc:
    """Tests for get_idp() with the cadc entry."""

    def test_get_idp_cadc_name(self) -> None:
        """CADC entry exposes the expected name."""
        idp = get_idp("cadc")

        assert idp.name == "Canadian Astronomy Data Centre"

    def test_get_idp_cadc_auth_mode(self) -> None:
        """CADC entry uses x509 authentication."""
        idp = get_idp("cadc")

        assert idp.auth_mode == "x509"

    def test_get_idp_cadc_registry_url(self) -> None:
        """CADC entry points at the CADC registry resource-caps URL."""
        idp = get_idp("cadc")

        assert (
            str(idp.registry_url)
            == "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps"
        )

    def test_get_idp_cadc_key(self) -> None:
        """CADC entry preserves the canonical key."""
        idp = get_idp("cadc")

        assert idp.key == "cadc"


class TestGetIdpSrcnet:
    """Tests for get_idp() with the srcnet entry."""

    def test_get_idp_srcnet_name(self) -> None:
        """SRCNet entry exposes the expected name."""
        idp = get_idp("srcnet")

        assert idp.name == "SKA Regional Centre Network"

    def test_get_idp_srcnet_auth_mode(self) -> None:
        """SRCNet entry uses oidc authentication."""
        idp = get_idp("srcnet")

        assert idp.auth_mode == "oidc"

    def test_get_idp_srcnet_registry_url(self) -> None:
        """SRCNet entry points at the SRCNet registry resource-caps URL."""
        idp = get_idp("srcnet")

        assert str(idp.registry_url) == "https://spsrc27.iaa.csic.es/reg/resource-caps"

    def test_get_idp_srcnet_key(self) -> None:
        """SRCNet entry preserves the canonical key."""
        idp = get_idp("srcnet")

        assert idp.key == "srcnet"


class TestGetIdpUnknown:
    """Tests for get_idp() with unknown keys."""

    def test_get_idp_unknown_raises_key_error(self) -> None:
        """Unknown IDP keys raise KeyError."""
        with pytest.raises(KeyError, match="unknown"):
            get_idp("unknown")


class TestIsValidIdp:
    """Tests for is_valid_idp()."""

    def test_is_valid_idp_cadc(self) -> None:
        """Canonical cadc key is valid."""
        assert is_valid_idp("cadc") is True

    def test_is_valid_idp_srcnet(self) -> None:
        """Canonical srcnet key is valid."""
        assert is_valid_idp("srcnet") is True

    def test_is_valid_idp_unknown(self) -> None:
        """Unknown keys are not valid."""
        assert is_valid_idp("unknown") is False


class TestIdpInfoModel:
    """Tests for the IdpInfo Pydantic model."""

    def test_idp_info_rejects_extra_fields(self) -> None:
        """IdpInfo forbids undeclared fields."""
        with pytest.raises(ValueError, match="extra"):
            IdpInfo(
                key="cadc",
                name="CADC",
                auth_mode="x509",
                registry_url="https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps",
                unexpected="value",
            )
