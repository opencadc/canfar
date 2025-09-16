"""CANFAR Science Platform Python Client."""

from os import environ as env
from pathlib import Path

from .utils.logging import configure_logging, get_logger, set_log_level

# Configuration paths and defaults
CONFIG_PATH: Path = Path.home() / ".canfar" / "config.yaml"
CERT_PATH: Path = Path.home() / ".ssl" / "cadcproxy.pem"
LOG_LEVEL: str = env.get("CANFAR_LOGLEVEL", "INFO")

configure_logging(loglevel=LOG_LEVEL, filelog=False)
log = get_logger(__name__)
set_log_level(LOG_LEVEL)

# Kept in sync with pyproject.toml by release-please
# DO NOT EDIT MANUALLY
__version__: str = "1.0.2"  # x-release-please-version

__all__ = ["__version__", "configure_logging", "get_logger", "set_log_level"]
