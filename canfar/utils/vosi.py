from __future__ import annotations

import re
from collections import OrderedDict
from typing import TypedDict, cast

import httpx
from defusedxml import ElementTree

# --- Constants & helpers ------------------------------------------------------

LEGACY_SESSIONS_STDID = "vos://cadc.nrc.ca~vospace/CADC/std/Proc#sessions-1.0"
PLATFORM_PREFIX = "http://www.opencadc.org/std/platform#session-"

# Auth mode rename map
AUTH_RENAME = {
    "token": "oidc",
    "tls-with-certificate": "x509",
}

# Preferred ordering (after rename)
AUTH_PRIORITY = {
    "x509": 0,
    "oidc": 1,
}

_VSEG_RE = re.compile(r"/(v[0-9]+(?:\.[0-9]+)*)\b")


class Capability(TypedDict):
    """Parsed Sessions capability family entry."""

    baseurl: str
    version: str | None
    auth_modes: list[str]


def _normalize_auth_id(standard_id: str) -> str:
    """Extract and normalize an auth mode from a `securityMethod` standardID.

    Args:
        standard_id: The `standardID` attribute value.

    Returns:
        The normalized auth mode string (renamed if necessary).
    """
    raw = standard_id.split("#", 1)[-1] if "#" in standard_id else standard_id
    return AUTH_RENAME.get(raw, raw)


def _split_base_and_version_from_url(url: str) -> tuple[str, str | None]:
    """Split an access URL into (baseurl, version).

    Args:
        url: The access URL text.

    Returns:
        A tuple of (baseurl, version) where version is like 'v1' or 'v1.2',
        or None if a '/vN' segment is not present.
    """
    u = (url or "").strip()
    u = re.sub(r"\s+", "", u)  # guard against accidental newlines/whitespace
    u = u.rstrip("/")
    m = _VSEG_RE.search(u)
    if not m:
        return u, None
    version = m.group(1)
    base = u[: m.start()]
    return base, version


def _major_from_standard_id(std_id: str | None) -> str | None:
    """Infer a major version label (e.g., 'v0', 'v1', 'v2') from a capability ID.

    Args:
        std_id: The `standardID` attribute of the capability element.

    Returns:
        A string like 'v0', 'v1', 'v2', or None if not derivable.
    """
    if not std_id:
        return None
    if std_id == LEGACY_SESSIONS_STDID:
        return "v0"
    if std_id.startswith(PLATFORM_PREFIX):
        tail = std_id[len(PLATFORM_PREFIX) :]
        m = re.match(r"([0-9]+)", tail)
        if m:
            return f"v{m.group(1)}"
    return None


def _is_sessions_capability(std_id: str | None) -> bool:
    """Check whether a capability standardID corresponds to 'sessions'."""
    if not std_id:
        return False
    return std_id == LEGACY_SESSIONS_STDID or std_id.startswith(PLATFORM_PREFIX)


def _sort_auth(modes: list[str]) -> list[str]:
    """Sort auth modes by a preferred priority (unknowns after knowns)."""
    return sorted(modes, key=lambda x: (AUTH_PRIORITY.get(x, 999), x))


def _parse_version_tuple(v: str | None) -> tuple[int, ...] | None:
    """Convert a version string like 'v2.1' or 'v1' into a numeric tuple."""
    if not v:
        return None
    m = re.fullmatch(r"v([0-9]+(?:\.[0-9]+)*)", v)
    if not m:
        return None
    return tuple(int(p) for p in m.group(1).split("."))


def _version_sort_key(v: str | None) -> tuple[int, tuple[int, ...]]:
    """Key for sorting versions (latest first)."""
    tup = _parse_version_tuple(v)
    if tup is None:
        return (1, (0,))
    return (0, tup)


def capabilities(url: str | None = None, xml: str | None = None) -> list[Capability]:  # noqa: PLR0912 too many branches (clarity)
    """Parse sessions capabilities into a list of endpoint families.

    Rules:
      * Legacy CADC sessions ('...Proc#sessions-1.0') are forced to 'v0'.
      * Platform sessions IDs ('.../platform#session-N') imply 'vN'.
      * If an accessURL contains '/vN', that version is used unless legacy.
      * Only `accessURL[use="base"]` is considered.
      * Auth modes are collected and deduplicated, with:
          - 'token' renamed to 'oidc'
          - 'tls-with-certificate' renamed to 'x509'
          - 'cookie' removed completely
      * Output is sorted by version (latest first).

    Args:
        url: A VOSI capabilities XML payload as a string.
        xml: A VOSI capabilities XML payload as a string.

    Returns:
        A list of dictionaries of the form:
        [
            {
                "baseurl": str,
                "version": Optional[str],
                "auth_modes": List[str],
            },
            ...
        ]
    """
    if xml:
        root = ElementTree.fromstring(xml)
    elif url:
        xml = httpx.get(url).text
    else:
        msg = "Either url or xml must be provided"
        raise ValueError(msg)
    root = ElementTree.fromstring(xml)
    buckets: OrderedDict[tuple[str, str | None], Capability] = OrderedDict()

    for cap in root.findall(".//{*}capability"):
        std_id = cap.get("standardID")
        if not _is_sessions_capability(std_id):
            continue

        std_major = _major_from_standard_id(std_id)

        for iface in cap.findall(".//{*}interface"):
            base_urls = [
                access
                for access in iface.findall("{*}accessURL")
                if access.get("use") == "base" and (access.text or "").strip()
            ]
            if not base_urls:
                continue

            # Element.text is Optional[str]; guarded above, cast for type-checking
            base_text = cast("str", base_urls[0].text)
            baseurl, url_major = _split_base_and_version_from_url(base_text)

            if std_major == "v0":
                version: str | None = "v0"
            elif url_major is not None:
                version = url_major
            else:
                version = std_major

            key = (baseurl, version)
            bucket = buckets.get(key)
            if not bucket:
                bucket = Capability(baseurl=baseurl, version=version, auth_modes=[])
                buckets[key] = bucket

            for sec in iface.findall("{*}securityMethod"):
                sid = sec.get("standardID")
                if not sid:
                    continue
                mode = _normalize_auth_id(sid)
                if mode == "cookie":
                    continue
                if mode not in bucket["auth_modes"]:
                    bucket["auth_modes"].append(mode)

    for b in buckets.values():
        b["auth_modes"] = _sort_auth(b["auth_modes"])

    items: list[Capability] = list(buckets.values())

    def sort_key(item: Capability) -> tuple[int, tuple[int, ...], str]:
        v = item.get("version")
        marker, tup = _version_sort_key(v)
        return (marker, tup, item["baseurl"])

    items.sort(key=sort_key, reverse=True)
    return items
