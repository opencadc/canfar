"""CANFAR Science Platform Python Client."""

from os import environ as env
from pathlib import Path

# Configuration paths and defaults (defined before logging import to avoid cycles)
CONFIG_DIR: Path = Path.home() / ".canfar"
CONFIG_PATH: Path = CONFIG_DIR / "config.yaml"

from .utils.logging import (  # noqa: E402
    configure_logging,
    get_logger,
    set_log_level,
)

CERT_PATH: Path = Path.home() / ".ssl" / "cadcproxy.pem"
LOG_LEVEL: str = env.get("CANFAR_LOGLEVEL", "INFO")

configure_logging(loglevel=LOG_LEVEL, filelog=False)
log = get_logger(__name__)
set_log_level(LOG_LEVEL)

from . import authentication, server  # noqa: E402
from .authentication import login  # noqa: E402

# Kept in sync with pyproject.toml by release-please
# DO NOT EDIT MANUALLY
__version__: str = "1.4.0"  # x-release-please-version

__all__ = [
    "CONFIG_DIR",
    "CONFIG_PATH",
    "__version__",
    "authentication",
    "configure_logging",
    "get_logger",
    "login",
    "server",
    "set_log_level",
]
