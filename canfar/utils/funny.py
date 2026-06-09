"""Generate funny session names from scientist surnames."""

from __future__ import annotations

import functools
import importlib.resources
import secrets


@functools.lru_cache(maxsize=1)
def _load_wordlist() -> tuple[str, ...]:
    """Load scientist surnames from the packaged data file.

    Returns:
        Tuple of lowercase ASCII scientist surnames.
    """
    path = importlib.resources.files("canfar.utils") / "data" / "scientists.txt"
    text = path.read_text(encoding="utf-8")
    return tuple(line.strip() for line in text.splitlines() if line.strip())


def name() -> str:
    """Generate a random scientist surname from the wordlist.

    Returns:
        A single lowercase ASCII scientist surname.
    """
    return secrets.choice(_load_wordlist())
