"""CANFAR Science Platform Python Client."""

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Configuration paths and defaults (defined before logging import to avoid cycles)
CONFIG_DIR: Path = Path.home() / ".canfar"
CONFIG_PATH: Path = CONFIG_DIR / "config.yaml"

from .utils.logging import (  # noqa: E402
    configure_logging,
    get_logger,
)

CERT_PATH: Path = Path.home() / ".ssl" / "cadcproxy.pem"

if TYPE_CHECKING:
    from . import authentication, server
    from .authentication import alogin, login

# Kept in sync with pyproject.toml by release-please
# DO NOT EDIT MANUALLY
__version__: str = "1.5.0"  # x-release-please-version

__all__ = [
    "CONFIG_DIR",
    "CONFIG_PATH",
    "__version__",
    "alogin",
    "authentication",
    "configure_logging",
    "get_logger",
    "login",
    "server",
]


def __getattr__(name: str) -> Any:
    """Import Authentication and Server operations on first use.

    Keeping them out of package import lets each CLI command and library entry
    point load only the HTTP and identity stack it needs.

    Raises:
        AttributeError: If ``name`` is not a lazy package attribute.
    """
    if name in {"authentication", "server"}:
        return import_module(f"{__name__}.{name}")
    if name in {"login", "alogin"}:
        return getattr(import_module(f"{__name__}.authentication"), name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
