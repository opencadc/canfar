"""Tests for the funny name generator."""

from __future__ import annotations

import importlib.resources
import re

from canfar.utils import funny

_NAME_PART = re.compile(r"^[a-z]{2,16}$")
_SINGLE_NAME = re.compile(r"^[a-z]+$")
_SESSION_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _load_scientists() -> list[str]:
    """Load scientist surnames from the packaged data file."""
    path = importlib.resources.files("canfar.utils") / "data" / "scientists.txt"
    text = path.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


def test_scientists_wordlist_count_and_format() -> None:
    """Wordlist has 256 unique lowercase ASCII surnames."""
    scientists = _load_scientists()
    assert len(scientists) == 256
    assert len(set(scientists)) == 256
    assert all(_NAME_PART.fullmatch(name) for name in scientists)


def test_name_returns_single_token_from_list() -> None:
    """name() returns one lowercase surname from the wordlist."""
    scientists = set(_load_scientists())
    result = funny.name()
    assert _SINGLE_NAME.fullmatch(result)
    assert "-" not in result
    assert result in scientists


def test_name_varies_across_calls() -> None:
    """name() produces more than one distinct value."""
    names = {funny.name() for _ in range(50)}
    assert len(names) > 1


def test_name_valid_session_name() -> None:
    """name() output is valid as a lowercase session name."""
    result = funny.name()
    assert _SESSION_NAME.fullmatch(result)
