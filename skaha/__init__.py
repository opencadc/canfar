"""Science Platform Python Client."""

from importlib import metadata
from pathlib import Path

import toml

from .utils.logging import configure_logging, get_logger, set_log_level

# Root path to the Skaha Project
BASE_PATH: Path = Path(__file__).absolute().parent.parent
CONFIG_PATH: Path = Path.home() / ".skaha" / "config.yaml"
CERT_PATH: Path = Path.home() / ".ssl" / "cadcproxy.pem"
LOG_LEVEL: str = "INFO"

configure_logging(loglevel=LOG_LEVEL, filelog=False)
log = get_logger(__name__)
set_log_level(LOG_LEVEL)

__version__: str = "unknown"

try:
    __version__ = metadata.version("skaha")
except metadata.PackageNotFoundError as error:  # pragma: no cover
    log.warning(error)
    pyproject = toml.load(BASE_PATH / "pyproject.toml")
    __version__ = str(pyproject.get("project", {}).get("version", "unknown"))
except FileNotFoundError as error:  # pragma: no cover
    log.warning(error)
finally:
    log.debug("Client Version: %s", __version__)

__all__ = ["__version__", "configure_logging", "get_logger", "set_log_level"]
