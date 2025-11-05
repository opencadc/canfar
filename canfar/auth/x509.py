"""X509 Certificate Management Module.

This module provides functionality to obtain and inspect X509 PEM certificates
using the cadcutils.net.auth library as the backbone for X509 authentication.
"""

from __future__ import annotations

from datetime import datetime, timezone
from os import R_OK, access
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cadcutils.net.auth import Subject, get_cert  # type: ignore[import-untyped]
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from canfar import CERT_PATH, get_logger

if TYPE_CHECKING:
    from canfar.models import auth

log = get_logger(__name__)


class CertificateError(ValueError):
    """Raised when an X.509 certificate cannot be used."""


def _to_utc(value: datetime) -> datetime:
    """Return timezone aware datetime.

    Args:
        value (datetime): Input datetime.

    Returns:
        datetime: Timezone aware datetime.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _validity_window(cert: x509.Certificate) -> tuple[datetime, datetime]:
    """Return validity start/end datetimes in UTC.

    Args:
        cert (x509.Certificate): Certificate to inspect.

    Raises:
        CertificateError: If certificate is expired or not yet valid.

    Returns:
        tuple[datetime, datetime]: Validity start and end datetimes in UTC.
    """
    try:
        start = getattr(cert, "not_valid_before_utc", None) or cert.not_valid_before
        end = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after
    except AttributeError as err:  # pragma: no cover - defensive path
        msg = "Certificate is missing validity information."
        raise CertificateError(msg) from err

    return _to_utc(start), _to_utc(end)


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
        raise CertificateError(msg)


def gather(
    username: str | None = None,
    days_valid: int = 30,
    cert_path: Path | None = None,
) -> dict[str, Any]:
    """Gather user credentials and obtain X509 certificate.

    This function uses cadcutils.net.auth.get_cert as the backbone to obtain
    X509 certificates, similar to how the cadc-get-cert CLI tool works.

    Args:
        username (str, optional): Username for authentication. Will prompt if None.
            Defaults to None.
        days_valid (int): Number of days the certificate should be valid.
            Defaults to 30.
        cert_path (Path, optional): Path to save certificate.
            Defaults to ~/.ssl/cadcproxy.pem.

    Returns:
        dict[str, Any]: Dictionary with certificate info for canfar.config.auth.X509:
            - path (str): Path to PEM certificate file
            - expiry (float): Certificate expiry ctime

    Raises:
        ValueError: If certificate retrieval fails.

    Examples:
        >>> info = gather(username="myuser", days_valid=30)
        >>> print(f"Certificate saved to {info['path']}")
    """
    # Get credentials if not provided
    if not username:
        username = input("Username: ")

    # Set default path
    if cert_path is None:
        log.debug("Using default certificate path: ~/.ssl/cadcproxy.pem")
        cert_path = Path.home() / ".ssl" / "cadcproxy.pem"

    try:
        # Create subject for authentication
        subject = Subject(username=username)

        # Use cadcutils.net.auth.get_cert to obtain the certificate
        cert_content = get_cert(
            subject=subject,
            days_valid=days_valid,
        )

        # Ensure the directory exists
        cert_path.parent.mkdir(parents=True, exist_ok=True)

        # Write certificate to file with secure permissions
        cert_path.write_text(cert_content)
        cert_path.chmod(0o600)  # Read/write for owner only

        # Get certificate info for return
        return inspect(cert_path)

    except Exception as e:
        msg = f"Failed to obtain X509 certificate: {e}"
        raise ValueError(msg) from e


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

    if not access(destination, R_OK):
        msg = f"{destination} is not readable."
        raise PermissionError(msg)

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
        cert = x509.load_pem_x509_certificate(data, default_backend())
        valid_from, valid_until = _validity_window(cert)
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


def authenticate(config: auth.X509) -> auth.X509:
    """Authenticate using X509 certificate.

    Args:
        config (auth.X509): X509 configuration.

    Returns:
        auth.X509: X509 configuration.

    Raises:
        ValueError: If certificate cannot be read or parsed.
    """
    try:
        data = gather()
        config.path = data["path"]
        config.expiry = data["expiry"]
    except Exception as err:
        msg = f"Failed to authenticate with X509 certificate: {err}"
        raise ValueError(msg) from err

    return config
