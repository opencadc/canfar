"""Tests for the canfar.auth.x509 module."""

from __future__ import annotations

import datetime
import math
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from canfar.auth import x509 as x509_auth
from canfar.models.auth import X509


# Helper function to generate a self-signed certificate for testing
def generate_cert(
    cert_path: Path,
    valid_for_days: int = 1,
    not_before_days: int = 0,
    expired: bool = False,
) -> None:
    """Generates a self-signed PEM certificate for testing purposes."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CA"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "BC"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Victoria"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Inc"),
            x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com"),
        ]
    )

    now = datetime.datetime.now(datetime.timezone.utc)

    if expired:
        not_valid_before = now - datetime.timedelta(days=30)
        not_valid_after = now - datetime.timedelta(days=15)
    else:
        not_valid_before = now + datetime.timedelta(days=not_before_days)
        not_valid_after = not_valid_before + datetime.timedelta(days=valid_for_days)

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before)
        .not_valid_after(not_valid_after)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    )

    certificate = builder.sign(private_key, hashes.SHA256())

    with cert_path.open("wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        f.write(certificate.public_bytes(serialization.Encoding.PEM))


# --- Tests for canfar.auth.x509.valid --- #


def test_valid_happy_path() -> None:
    """Test that `valid` returns the correct path for a valid certificate."""
    with tempfile.NamedTemporaryFile(suffix=".pem") as temp_cert:
        cert_path = Path(temp_cert.name)
        generate_cert(cert_path)
        result = x509_auth.valid(cert_path)
        assert Path(result).resolve() == cert_path.resolve()


def test_valid_file_not_found() -> None:
    """Test that `valid` raises FileNotFoundError for a non-existent file."""
    non_existent_path = Path("/this/path/does/not.exist")
    with pytest.raises(FileNotFoundError):
        x509_auth.valid(non_existent_path)


def test_valid_not_a_file() -> None:
    """Test that `valid` raises ValueError for a path that is a directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        with pytest.raises(ValueError, match="is not a file"):
            x509_auth.valid(dir_path)


def test_valid_not_readable(tmp_path) -> None:
    """Test that `valid` raises PermissionError for an unreadable file."""
    cert_path = tmp_path / "cert.pem"
    generate_cert(cert_path)
    cert_path.chmod(0o000)  # Make the file unreadable
    with pytest.raises(PermissionError, match="is not readable"):
        x509_auth.valid(cert_path)
    cert_path.chmod(0o600)  # Clean up permissions


# --- Tests for canfar.auth.x509.expiry --- #


def test_expiry_happy_path() -> None:
    """Test that `expiry` returns the correct expiry timestamp for a valid cert."""
    with tempfile.NamedTemporaryFile(suffix=".pem") as temp_cert:
        cert_path = Path(temp_cert.name)
        generate_cert(cert_path, valid_for_days=5)
        expiry_ts = x509_auth.expiry(cert_path)
        assert isinstance(expiry_ts, float)
        assert expiry_ts > datetime.datetime.now(datetime.timezone.utc).timestamp()


def test_expiry_not_yet_valid() -> None:
    """Test that `expiry` raises ValueError for a certificate that is not yet valid."""
    with tempfile.NamedTemporaryFile(suffix=".pem") as temp_cert:
        cert_path = Path(temp_cert.name)
        generate_cert(cert_path, not_before_days=2)
        with pytest.raises(ValueError, match="is not yet valid."):
            x509_auth.expiry(cert_path)


def test_expiry_with_invalid_content() -> None:
    """Test that `expiry` raises ValueError for a file with invalid content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem") as temp_cert:
        temp_cert.write("this is not a valid certificate")
        temp_cert.flush()
        cert_path = Path(temp_cert.name)
        with pytest.raises(ValueError, match="Unable to load PEM file."):
            x509_auth.expiry(cert_path)


# --- Tests for canfar.auth.x509.inspect --- #


def test_inspect_happy_path() -> None:
    """Test that `inspect` returns the correct path and expiry."""
    with tempfile.NamedTemporaryFile(suffix=".pem") as temp_cert:
        cert_path = Path(temp_cert.name)
        generate_cert(cert_path)

        result = x509_auth.inspect(cert_path)

        assert "path" in result
        assert "expiry" in result
        assert Path(result["path"]).resolve() == cert_path.resolve()
        assert isinstance(result["expiry"], float)
        assert (
            result["expiry"] > datetime.datetime.now(datetime.timezone.utc).timestamp()
        )


# --- Tests for canfar.auth.x509.authenticate --- #


@patch("canfar.auth.x509.gather")
def test_authenticate_happy_path(mock_gather) -> None:
    """Test that `authenticate` correctly updates the config on success."""
    with tempfile.NamedTemporaryFile(suffix=".pem") as temp_cert:
        cert_path = Path(temp_cert.name)
        generate_cert(cert_path)

        mock_gather.return_value = {
            "path": str(cert_path.resolve()),
            "expiry": datetime.datetime.now(datetime.timezone.utc).timestamp() + 1000,
        }

        config = X509()
        updated_config = x509_auth.authenticate(config)

        assert updated_config.path == str(cert_path.resolve())
        assert updated_config.expiry == mock_gather.return_value["expiry"]
        mock_gather.assert_called_once()


@patch("canfar.auth.x509.gather")
def test_authenticate_gather_fails(mock_gather) -> None:
    """Test that `authenticate` raises a ValueError if `gather` fails."""
    mock_gather.side_effect = ValueError("Failed to retrieve certificate")

    config = X509()
    with pytest.raises(ValueError, match="Failed to authenticate"):
        x509_auth.authenticate(config)


# --- Tests for canfar.auth.x509.gather --- #


@patch("canfar.auth.x509.get_cert")
@patch("canfar.auth.x509.inspect")
def test_gather_happy_path(mock_inspect, mock_get_cert, tmp_path) -> None:
    """Test the happy path for `gather` with a username provided."""
    mock_get_cert.return_value = "---BEGIN CERT---...---END CERT---"
    cert_path = tmp_path / "test.pem"
    mock_inspect.return_value = {"path": str(cert_path), "expiry": 12345.67}

    result = x509_auth.gather(username="testuser", cert_path=cert_path)

    assert result["path"] == str(cert_path)
    assert math.isclose(result["expiry"], 12345.67, abs_tol=1e-9)
    mock_get_cert.assert_called_once()
    assert cert_path.exists()
    assert cert_path.read_text() == "---BEGIN CERT---...---END CERT---"


@patch("builtins.input")
@patch("canfar.auth.x509.get_cert")
@patch("canfar.auth.x509.inspect")
def test_gather_prompts_for_username(
    mock_inspect, mock_get_cert, mock_input, tmp_path
) -> None:
    """Test that `gather` prompts for a username if not provided."""
    mock_input.return_value = "prompted_user"
    mock_get_cert.return_value = "---BEGIN CERT---...---END CERT---"
    cert_path = tmp_path / "test.pem"
    mock_inspect.return_value = {"path": str(cert_path), "expiry": 12345.67}

    x509_auth.gather(cert_path=cert_path)

    mock_input.assert_called_once_with("Username: ")
    subject_arg = mock_get_cert.call_args[1]["subject"]
    assert subject_arg.username == "prompted_user"


@patch("pathlib.Path.home")
@patch("canfar.auth.x509.get_cert")
@patch("canfar.auth.x509.inspect")
def test_gather_uses_default_path(
    mock_inspect, mock_get_cert, mock_home, tmp_path
) -> None:
    """Test that `gather` uses the default certificate path if none is provided."""
    # Point Path.home() to the pytest temporary directory
    mock_home.return_value = tmp_path
    mock_get_cert.return_value = "---BEGIN CERT---...---END CERT---"

    expected_path = tmp_path / ".ssl" / "cadcproxy.pem"
    mock_inspect.return_value = {"path": str(expected_path), "expiry": 12345.67}

    # Run the function without a path
    result = x509_auth.gather(username="testuser")

    # Verify the result from the mocked inspect call
    assert result["path"] == str(expected_path)

    # Verify that the file was actually created with the correct content and permissions
    assert expected_path.exists()
    assert expected_path.read_text() == "---BEGIN CERT---...---END CERT---"
    assert (expected_path.stat().st_mode & 0o777) == 0o600


@patch("canfar.auth.x509.get_cert")
def test_gather_get_cert_fails(mock_get_cert, tmp_path) -> None:
    """Test that `gather` raises a ValueError if `get_cert` fails."""
    mock_get_cert.side_effect = Exception("Network error")
    cert_path = tmp_path / "test.pem"

    with pytest.raises(ValueError, match="Failed to obtain X509 certificate"):
        x509_auth.gather(username="testuser", cert_path=cert_path)
