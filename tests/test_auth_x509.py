"""Tests for the canfar.auth.x509 module."""

from __future__ import annotations

import base64
import datetime
import math
import tempfile
from functools import partial
from pathlib import Path
from unittest.mock import patch

import httpx2
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from canfar.auth import x509 as x509_auth
from canfar.models.auth import X509Credential


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
        with pytest.raises(x509_auth.CertificateError, match="valid from"):
            x509_auth.expiry(cert_path)


def test_expiry_exposes_expiration_time(tmp_path) -> None:
    """Expired certificates expose their end time for human-facing diagnostics."""
    cert_path = tmp_path / "expired.pem"
    generate_cert(cert_path, expired=True)

    with pytest.raises(x509_auth.CertificateError) as excinfo:
        x509_auth.expiry(cert_path)

    assert excinfo.value.expired_at is not None
    assert excinfo.value.expired_at < datetime.datetime.now(datetime.timezone.utc)


def test_expiry_with_invalid_content() -> None:
    """Test that `expiry` raises ValueError for a file with invalid content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem") as temp_cert:
        temp_cert.write("this is not a valid certificate")
        temp_cert.flush()
        cert_path = Path(temp_cert.name)
        with pytest.raises(x509_auth.CertificateError, match="Unable to load PEM file"):
            x509_auth.expiry(cert_path)


def test_expiry_error_message_contains_times(tmp_path) -> None:
    """Ensure the error message includes validity window and current time."""
    cert_path = tmp_path / "future.pem"
    generate_cert(cert_path, not_before_days=2, valid_for_days=5)
    with pytest.raises(x509_auth.CertificateError) as excinfo:
        x509_auth.expiry(cert_path)

    message = str(excinfo.value)
    assert "valid from" in message
    assert "until" in message
    assert "current time" in message


def test_expiry_uses_current_cryptography_certificate_api(
    monkeypatch, tmp_path
) -> None:
    """Expiry reads certificates through the current Cryptography API."""
    cert_path = tmp_path / "cert.pem"
    generate_cert(cert_path, valid_for_days=3)

    original_loader = x509_auth.x509.load_pem_x509_certificate
    original_cert = original_loader(cert_path.read_bytes())

    class ModernCertificate:
        """Certificate exposing only the supported UTC-aware validity fields."""

        not_valid_before_utc = original_cert.not_valid_before_utc
        not_valid_after_utc = original_cert.not_valid_after_utc

    def load_certificate(data: bytes) -> ModernCertificate:
        assert data == cert_path.read_bytes()
        return ModernCertificate()

    monkeypatch.setattr(
        x509_auth.x509,
        "load_pem_x509_certificate",
        load_certificate,
    )

    expiry_ts = x509_auth.expiry(cert_path)
    assert expiry_ts == pytest.approx(original_cert.not_valid_after_utc.timestamp())


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


# --- Tests for canfar.auth.x509.authenticate_credential --- #


@patch("canfar.auth.x509.gather")
def test_authenticate_credential_happy_path(mock_gather) -> None:
    """Test that `authenticate_credential` correctly updates the credential."""
    with tempfile.NamedTemporaryFile(suffix=".pem") as temp_cert:
        cert_path = Path(temp_cert.name)
        generate_cert(cert_path)

        mock_gather.return_value = {
            "path": str(cert_path.resolve()),
            "expiry": datetime.datetime.now(datetime.timezone.utc).timestamp() + 1000,
        }

        credential = X509Credential(idp="test")
        updated = x509_auth.authenticate_credential(credential)

        assert updated is credential
        assert str(updated.path) == str(cert_path.resolve())
        assert updated.expiry == mock_gather.return_value["expiry"]
        mock_gather.assert_called_once()


@patch("canfar.auth.x509.gather")
def test_authenticate_credential_gather_fails(mock_gather) -> None:
    """Test that `authenticate_credential` raises ValueError if `gather` fails."""
    mock_gather.side_effect = ValueError("Failed to retrieve certificate")

    credential = X509Credential(idp="test")
    with pytest.raises(ValueError, match="Failed to authenticate"):
        x509_auth.authenticate_credential(credential)


# --- Tests for canfar.auth.x509.gather --- #


_PEM = "---BEGIN CERT---...---END CERT---"
_REGISTRY = "https://cadc-west-01.canfar.net/reg/resource-caps"
_CAPABILITIES = "https://cred.example/cred/capabilities"
_GENERATE = "https://cred.example/cred/generate"


def _cred_capabilities(*methods: str) -> str:
    security = "".join(
        f'<securityMethod standardID="ivo://ivoa.net/sso#{method}"/>'
        for method in methods
    )
    return (
        '<vosi:capabilities xmlns:vosi="http://www.ivoa.net/xml/VOSICapabilities/v1.0">'
        '<capability standardID="ivo://ivoa.net/std/CDP#proxy-1.0">'
        f'<interface><accessURL use="base">{_GENERATE}</accessURL>{security}'
        "</interface></capability></vosi:capabilities>"
    )


def _basic(username: str, password: str) -> str:
    return "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()


@pytest.fixture
def cred_service(monkeypatch: pytest.MonkeyPatch) -> list[httpx2.Request]:
    """Serve the CADC registry and credential service; record each request."""
    requests: list[httpx2.Request] = []
    pages = {
        _REGISTRY: f"ivo://cadc.nrc.ca/cred = {_CAPABILITIES}\n",
        _CAPABILITIES: _cred_capabilities("tls-with-certificate", "BasicAA"),
        _GENERATE: _PEM,
    }

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        url = str(request.url.copy_with(query=None))
        return httpx2.Response(200, text=pages[url])

    monkeypatch.setattr(
        "httpx2.Client",
        partial(httpx2.Client, transport=httpx2.MockTransport(handler)),
    )
    monkeypatch.setattr("getpass.getpass", lambda _prompt: "secret")
    return requests


@patch("canfar.auth.x509.inspect")
def test_gather_requests_a_certificate_with_the_password(
    mock_inspect, cred_service, tmp_path
) -> None:
    """``gather`` finds the CDP endpoint and saves the certificate it issues."""
    cert_path = tmp_path / "test.pem"
    mock_inspect.return_value = {"path": str(cert_path), "expiry": 12345.67}

    result = x509_auth.gather(username="testuser", cert_path=cert_path)

    assert result["path"] == str(cert_path)
    assert math.isclose(result["expiry"], 12345.67, abs_tol=1e-9)
    generate = cred_service[-1]
    assert generate.url.params["daysValid"] == "30"
    assert generate.headers["Authorization"] == _basic("testuser", "secret")
    assert cert_path.read_text() == _PEM


@patch("builtins.input")
@patch("canfar.auth.x509.inspect")
def test_gather_prompts_for_username(
    mock_inspect, mock_input, cred_service, tmp_path
) -> None:
    """Test that `gather` prompts for a username if not provided."""
    mock_input.return_value = "prompted_user"
    cert_path = tmp_path / "test.pem"
    mock_inspect.return_value = {"path": str(cert_path), "expiry": 12345.67}

    x509_auth.gather(cert_path=cert_path)

    mock_input.assert_called_once_with("Username: ")
    assert cred_service[-1].headers["Authorization"] == _basic(
        "prompted_user", "secret"
    )


@pytest.mark.usefixtures("cred_service")
@patch("pathlib.Path.home")
@patch("canfar.auth.x509.inspect")
def test_gather_uses_default_path(mock_inspect, mock_home, tmp_path) -> None:
    """Test that `gather` uses the default certificate path if none is provided."""
    mock_home.return_value = tmp_path
    expected_path = tmp_path / ".ssl" / "cadcproxy.pem"
    mock_inspect.return_value = {"path": str(expected_path), "expiry": 12345.67}

    result = x509_auth.gather(username="testuser")

    assert result["path"] == str(expected_path)
    assert expected_path.read_text() == _PEM
    assert (expected_path.stat().st_mode & 0o777) == 0o600


def test_gather_rejects_an_empty_password(cred_service, monkeypatch, tmp_path) -> None:
    """An empty password fails before any request."""
    monkeypatch.setattr("getpass.getpass", lambda _prompt: "")

    with pytest.raises(ValueError, match="Password cannot be empty"):
        x509_auth.gather(username="testuser", cert_path=tmp_path / "test.pem")

    assert cred_service == []


def test_gather_requires_password_login(monkeypatch, tmp_path) -> None:
    """A credential service without BasicAA cannot issue a certificate here."""
    pages = {
        _REGISTRY: f"ivo://cadc.nrc.ca/cred = {_CAPABILITIES}",
        _CAPABILITIES: _cred_capabilities("tls-with-certificate"),
    }
    monkeypatch.setattr("getpass.getpass", lambda _prompt: "secret")
    monkeypatch.setattr(
        "httpx2.Client",
        partial(
            httpx2.Client,
            transport=httpx2.MockTransport(
                lambda request: httpx2.Response(200, text=pages[str(request.url)])
            ),
        ),
    )
    cert_path = tmp_path / "test.pem"

    with pytest.raises(ValueError, match="offers no password login"):
        x509_auth.gather(username="testuser", cert_path=cert_path)
    assert not cert_path.exists()


def test_gather_wraps_http_errors(monkeypatch, tmp_path) -> None:
    """Test that `gather` raises a ValueError if the service rejects the login."""
    monkeypatch.setattr("getpass.getpass", lambda _prompt: "wrong")
    monkeypatch.setattr(
        "httpx2.Client",
        partial(
            httpx2.Client,
            transport=httpx2.MockTransport(lambda _request: httpx2.Response(401)),
        ),
    )

    with pytest.raises(ValueError, match="Failed to obtain X509 certificate"):
        x509_auth.gather(username="testuser", cert_path=tmp_path / "test.pem")
