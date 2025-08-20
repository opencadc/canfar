"""Tests for the VOSI utilities module."""

import pytest

from canfar.utils.vosi import capabilities


@pytest.fixture
def samples() -> list[tuple[str, str]]:
    """Provide sample capabilities data for testing."""
    samples: list[tuple[str, str]] = []
    samples.append(
        (
            "case1",
            """
            <vosi:capabilities xmlns:vosi="http://www.ivoa.net/xml/VOSICapabilities/v1.0"
                xmlns:vr="http://www.ivoa.net/xml/VOResource/v1.0"
                xmlns:vs="http://www.ivoa.net/xml/VODataService/v1.1"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <capability standardID="vos://cadc.nrc.ca~vospace/CADC/std/Proc#sessions-1.0">
                <interface xsi:type="vs:ParamHTTP" role="std" version="1.0">
                <accessURL use="base">https://src.canfar.net/skaha/v0</accessURL>
                </interface>
                <interface xsi:type="vs:ParamHTTP" role="std" version="1.0">
                <accessURL use="base">https://src.canfar.net/skaha/v0</accessURL>
                </interface>
                <interface xsi:type="vs:ParamHTTP" role="std" version="1.0">
                <accessURL use="base">https://src.canfar.net/skaha/v0</accessURL>
                <securityMethod standardID="ivo://ivoa.net/sso#token"/>
                </interface>
            </capability>
            </vosi:capabilities>
    """.strip(),
        )
    )
    samples.append(
        (
            "case2",
            """
            <vosi:capabilities xmlns:vosi="http://www.ivoa.net/xml/VOSICapabilities/v1.0"
                xmlns:vr="http://www.ivoa.net/xml/VOResource/v1.0"
                xmlns:vs="http://www.ivoa.net/xml/VODataService/v1.1"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <capability standardID="vos://cadc.nrc.ca~vospace/CADC/std/Proc#sessions-1.0">
                <interface xsi:type="vs:ParamHTTP" role="std" version="1.0">
                <accessURL use="base">https://services.swesrc.chalmers.se/skaha/v0</accessURL>
                </interface>
                <interface xsi:type="vs:ParamHTTP" role="std" version="1.0">
                <accessURL use="base">https://services.swesrc.chalmers.se/skaha/v0</accessURL>
                </interface>
                <interface xsi:type="vs:ParamHTTP" role="std" version="1.0">
                <accessURL use="base">https://services.swesrc.chalmers.se/skaha/v0</accessURL>
                <securityMethod standardID="ivo://ivoa.net/sso#token"/>
                </interface>
            </capability>
            </vosi:capabilities>
    """.strip(),
        )
    )
    samples.append(
        (
            "case3",
            """
            <vosi:capabilities xmlns:vosi="http://www.ivoa.net/xml/VOSICapabilities/v1.0"
                xmlns:vr="http://www.ivoa.net/xml/VOResource/v1.0"
                xmlns:vs="http://www.ivoa.net/xml/VODataService/v1.1"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <capability standardID="vos://cadc.nrc.ca~vospace/CADC/std/Proc#sessions-1.0">
                <interface xsi:type="vs:ParamHTTP" role="std" version="1.0">
                <accessURL use="base">https://canfar.cam.uksrc.org/skaha/v0</accessURL>
                </interface>
                <interface xsi:type="vs:ParamHTTP" role="std" version="1.0">
                <accessURL use="base">https://canfar.cam.uksrc.org/skaha/v0</accessURL>
                </interface>
                <interface xsi:type="vs:ParamHTTP" role="std" version="1.0">
                <accessURL use="base">https://canfar.cam.uksrc.org/skaha/v0</accessURL>
                <securityMethod standardID="ivo://ivoa.net/sso#token"/>
                </interface>
            </capability>
            </vosi:capabilities>
    """.strip(),
        )
    )
    return samples


def test_capabilities(samples: list[tuple[str, str]]) -> None:
    expected = {
        "case3": [
            {
                "baseurl": "https://canfar.cam.uksrc.org/skaha",
                "version": "v0",
                "auth_modes": ["oidc"],
            }
        ],
        "case2": [
            {
                "baseurl": "https://services.swesrc.chalmers.se/skaha",
                "version": "v0",
                "auth_modes": ["oidc"],
            }
        ],
        "case1": [
            {
                "baseurl": "https://src.canfar.net/skaha",
                "version": "v0",
                "auth_modes": ["oidc"],
            }
        ],
    }

    for name, xml in samples:
        caps = capabilities(xml=xml)
        assert caps, f"Failed to parse {name}"
        assert expected[name] == caps, f"Failed to parse {name}"
