"""X509 Certificate Management Module.

This module obtains CADC proxy certificates from the CADC credential service
and inspects X509 PEM certificates.
"""

from __future__ import annotations

import getpass
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cryptography import x509
from defusedxml import ElementTree

from canfar import CERT_PATH, __version__
from canfar.idp import get_idp

if TYPE_CHECKING:
    import httpx2

    from canfar.models.auth import X509Credential

log = logging.getLogger(__name__)

_CREDENTIAL_SERVICE = "ivo://cadc.nrc.ca/cred"
_CDP_PROXY = "ivo://ivoa.net/std/CDP#proxy-1.0"
_BASIC_AA = "ivo://ivoa.net/sso#BasicAA"
_DAYS_VALID = 30
_CDP_TIMEOUT = 30


class CertificateError(ValueError):
    """Raised when an X.509 certificate cannot be used."""

    def __init__(
        self,
        message: str,
        *,
        expired_at: datetime | None = None,
    ) -> None:
        """Initialize a certificate error with optional structured expiry."""
        super().__init__(message)
        self.expired_at = expired_at


def assert_valid_dates(
    destination: Path, valid_from: datetime, valid_until: datetime
) -> None:
    """Check if x509 cert dates are valid.

    Args:
        destination (Path): Path to certificate file.
        valid_from (datetime): Validity start datetime.
        valid_until (datetime): Validity end datetime.

    Raises:
        CertificateError: If certificate is expired or not yet valid.
    """
    now_utc = datetime.now(timezone.utc)
    if valid_from > now_utc:
        msg = (
            f"Certificate {destination} valid from {valid_from.isoformat()} "
            f"until {valid_until.isoformat()}; current time {now_utc.isoformat()}."
        )
        raise CertificateError(msg)

    if valid_until <= now_utc:
        msg = (
            f"Certificate {destination} expired on {valid_until.isoformat()}; "
            f"current time {now_utc.isoformat()}."
        )
        raise CertificateError(msg, expired_at=valid_until)


def gather(
    username: str | None = None,
    cert_path: Path | None = None,
) -> dict[str, Any]:
    """Prompt for CADC credentials and save a new proxy certificate.

    The CADC credential service issues a certificate valid for 30 days through
    the IVOA Credential Delegation Protocol (CDP), as ``cadc-get-cert`` does.

    Args:
        username (str, optional): CADC username. Prompts when omitted.
        cert_path (Path, optional): Path to save the certificate.
            Defaults to ~/.ssl/cadcproxy.pem.

    Returns:
        dict[str, Any]: Dictionary with certificate info for canfar.config.auth.X509:
            - path (str): Path to PEM certificate file
            - expiry (float): Certificate expiry ctime

    Raises:
        ValueError: If certificate retrieval fails.

    Examples:
        >>> info = gather(username="myuser")
        >>> print(f"Certificate saved to {info['path']}")
    """
    if not username:
        username = input("Username: ")
    if cert_path is None:
        cert_path = Path.home() / ".ssl" / "cadcproxy.pem"

    # httpx2 loads only to fetch a certificate, keeping CLI startup light.
    import httpx2  # noqa: PLC0415

    password = getpass.getpass("Password: ")
    if not password:
        msg = "Failed to obtain X509 certificate: Password cannot be empty"
        raise ValueError(msg)
    try:
        with httpx2.Client(
            headers={"User-Agent": f"python-canfar/{__version__}"},
            timeout=_CDP_TIMEOUT,
        ) as client:
            response = client.get(
                _certificate_url(client),
                params={"daysValid": _DAYS_VALID},
                auth=(username, password),
            )
            response.raise_for_status()
        cert_path.parent.mkdir(parents=True, exist_ok=True)
        cert_path.write_text(response.text)
        cert_path.chmod(0o600)
        return inspect(cert_path)
    except Exception as e:
        msg = f"Failed to obtain X509 certificate: {e}"
        raise ValueError(msg) from e


def _certificate_url(client: httpx2.Client) -> str:
    """Resolve the CADC credential service's password-authenticated CDP URL."""
    response = client.get(str(get_idp("cadc").registry_url))
    response.raise_for_status()
    for line in response.text.splitlines():
        uri, _, url = line.partition("=")
        if uri.strip() == _CREDENTIAL_SERVICE:
            break
    else:
        msg = f"The CADC registry does not list {_CREDENTIAL_SERVICE}."
        raise ValueError(msg)

    response = client.get(url.strip())
    response.raise_for_status()
    for capability in ElementTree.fromstring(response.text).findall(".//{*}capability"):
        if capability.get("standardID") != _CDP_PROXY:
            continue
        for interface in capability.findall("{*}interface"):
            methods = {
                sm.get("standardID") for sm in interface.findall("{*}securityMethod")
            }
            access = interface.findtext("{*}accessURL")
            if _BASIC_AA in methods and access:
                return access.strip()
    msg = f"{_CREDENTIAL_SERVICE} offers no password login for certificates."
    raise ValueError(msg)


def inspect(path: Path = CERT_PATH) -> dict[str, Any]:
    """Inspect X509 certificate and return info for canfar.config.auth.X509.

    Args:
        path (Path, optional): Path to certificate file.
            Defaults to canfar.CERT_PATH, which is ~/.ssl/cadcproxy.pem.

    Returns:
        dict[str, Any]: Dictionary with certificate info for canfar.config.auth.X509:
            - path (str): Path to PEM certificate file
            - expiry (float | None): Certificate expiry ctime

    Raises:
        ValueError: If certificate cannot be read or parsed.

    Examples:
        >>> info = inspect()
        >>> print(f"Certificate for {info['username']} expires at {info['expiry']}")
    """
    return {"path": valid(path), "expiry": expiry(path)}


def valid(path: Path = CERT_PATH) -> str:
    """Check if certificate exists and is readable.

    Args:
        path (Path, optional): Path to certificate file.
            Defaults to canfar.CERT_PATH, which is ~/.ssl/cadcproxy.pem.

    Returns:
        str: Absolute path to certificate file.

    Raises:
        FileNotFoundError: If certificate file does not exist.
        ValueError: If certificate file is not a file.
        PermissionError: If certificate file is not readable.
    """
    try:
        destination = path.resolve(strict=True)
    except FileNotFoundError as err:
        msg = f"{path.as_posix()} does not exist."
        raise FileNotFoundError(msg) from err

    if not destination.is_file():
        msg = f"{destination} is not a file."
        raise ValueError(msg)

    try:
        with destination.open("rb"):
            pass
    except PermissionError as err:
        msg = f"{destination} is not readable."
        raise PermissionError(msg) from err

    return destination.absolute().as_posix()


def expiry(path: Path = CERT_PATH) -> float:
    """Get the expiry time for the certificate.

    Expiry time is returned as a Unix timestamp (seconds since epoch).

    Args:
        path (Path, optional): Path to certificate file.
            Defaults to canfar.CERT_PATH, which is ~/.ssl/cadcproxy.pem.

    Returns:
        float: Expiry time as Unix timestamp (seconds since epoch).

    Raises:
        ValueError: If certificate is expired, not yet valid, or cannot be parsed.
    """
    try:
        destination = path.resolve(strict=True)
        data = destination.read_bytes()
        cert = x509.load_pem_x509_certificate(data)
        valid_from = cert.not_valid_before_utc
        valid_until = cert.not_valid_after_utc
        assert_valid_dates(destination, valid_from, valid_until)
        return valid_until.timestamp()
    except FileNotFoundError as err:
        msg = f"x509 cert not found: {err}"
        log.debug(msg)
        return 0.0
    except CertificateError:
        raise
    except Exception as err:
        msg = f"Unable to load PEM file at {path.as_posix()}. {err}"
        raise CertificateError(msg) from err


def authenticate_credential(credential: X509Credential) -> X509Credential:
    """Acquire and validate an X.509 Authentication Record."""
    try:
        data = gather()
        candidate = type(credential).model_validate(
            {
                "idp": credential.idp,
                "path": data["path"],
                "expiry": data["expiry"],
            }
        )
        credential.path, credential.expiry = candidate.path, candidate.expiry
    except Exception as err:
        msg = f"Failed to authenticate with X509 certificate: {err}"
        raise ValueError(msg) from err

    return credential
