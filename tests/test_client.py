"""Test CANFAR Python Client API."""
# ruff: noqa: SLF001

import ssl
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from pydantic import AnyHttpUrl, AnyUrl, SecretStr, ValidationError

from canfar.client import HTTPClient
from canfar.models.auth import OIDC, X509, Client, Endpoint, Expiry, Token
from canfar.models.config import Configuration
from canfar.models.http import Server
from canfar.models.registry import ContainerRegistry


# Test Fixtures
@pytest.fixture
def canfar_client_fixture():
    """Fixture that yields a HTTPClient instance for testing."""

    def _create_client(**kwargs):
        return HTTPClient(**kwargs)

    return _create_client


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.Client to prevent actual network calls."""
    with patch("httpx.Client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_httpx_async_client():
    """Mock httpx.AsyncClient to prevent actual network calls."""
    with patch("httpx.AsyncClient") as mock_async_client:
        yield mock_async_client


@pytest.fixture
def mock_cryptography():
    """Mock cryptography functions for certificate validation."""
    with patch("canfar.auth.x509.inspect") as mock_inspect:
        mock_inspect.return_value = {"expiry": 9999999999}  # Far future
        yield mock_inspect


class TestInitializationAndConfiguration:
    """Test HTTPClient initialization and configuration loading."""

    def test_default_initialization(self, canfar_client_fixture) -> None:
        """Test default initialization with no arguments."""
        client = canfar_client_fixture()
        assert client.timeout == 30
        assert client.concurrency == 32
        assert client.loglevel == "INFO"
        assert client.token is None
        assert client.certificate is None
        assert client.url is None
        assert isinstance(client.config, Configuration)

    def test_constructor_arguments(self, canfar_client_fixture) -> None:
        """Test initialization with explicit constructor arguments."""
        config = Configuration()
        client = canfar_client_fixture(
            timeout=60,
            concurrency=64,
            token=SecretStr("test-token"),
            certificate=Path("/test/cert.pem"),
            url="https://example.com/api",
            config=config,
            loglevel="DEBUG",
        )
        assert client.timeout == 60
        assert client.concurrency == 64
        assert client.token.get_secret_value() == "test-token"
        # Certificate should be None due to token precedence
        assert client.certificate is None
        assert str(client.url) == "https://example.com/api"
        assert client.config is config
        assert client.loglevel == "DEBUG"

    def test_environment_variables(self, canfar_client_fixture, monkeypatch) -> None:
        """Test that environment variables are picked up correctly."""
        monkeypatch.setenv("CANFAR_TIMEOUT", "45")
        monkeypatch.setenv("CANFAR_CONCURRENCY", "16")
        monkeypatch.setenv("CANFAR_TOKEN", "env-token")
        monkeypatch.setenv("CANFAR_URL", "https://env.example.com")
        monkeypatch.setenv("CANFAR_LOGLEVEL", "WARNING")

        client = canfar_client_fixture()
        assert client.timeout == 45
        assert client.concurrency == 16
        assert client.token.get_secret_value() == "env-token"
        # URL gets normalized with trailing slash
        assert str(client.url) == "https://env.example.com/"
        assert client.loglevel == "WARNING"

    def test_precedence_constructor_over_env(
        self, canfar_client_fixture, monkeypatch
    ) -> None:
        """Test that constructor arguments take precedence over env variables."""
        monkeypatch.setenv("CANFAR_TIMEOUT", "45")
        monkeypatch.setenv("CANFAR_TOKEN", "env-token")

        client = canfar_client_fixture(
            timeout=90,
            token=SecretStr("constructor-token"),
            url="https://example.com",  # Need URL when using token
        )
        assert client.timeout == 90
        assert client.token.get_secret_value() == "constructor-token"

    def test_client_has_session_attribute(self, canfar_client_fixture) -> None:
        """Test if HTTPClient object contains httpx.Client attribute."""
        client = canfar_client_fixture(
            token=SecretStr("test_token"), url="https://example.com"
        )
        assert hasattr(client, "client")
        assert isinstance(client.client, httpx.Client)

    def test_bad_server_no_schema(self, canfar_client_fixture) -> None:
        """Test server URL without schema."""
        with pytest.raises(ValidationError):
            canfar_client_fixture(url="ws-uv.canfar.net")

    def test_default_certificate(self, canfar_client_fixture) -> None:
        """Test validation with default certificate value."""
        try:
            canfar_client_fixture()
        except ValidationError as err:
            raise AssertionError from err
        assert True


class TestRuntimeCredentialHandling:
    """Test runtime credential handling including mutual exclusivity and validation."""

    def test_token_only(self, canfar_client_fixture) -> None:
        """Test instantiation with token only."""
        client = canfar_client_fixture(
            token=SecretStr("abc"), url="https://example.com"
        )
        assert client.token.get_secret_value() == "abc"
        assert client.certificate is None

    def test_certificate_only(self, canfar_client_fixture, tmp_path) -> None:
        """Test instantiation with certificate only."""
        cert_path = tmp_path / "test.pem"
        _create_test_certificate(cert_path)

        client = canfar_client_fixture(certificate=cert_path, url="https://example.com")
        assert client.certificate == cert_path
        assert client.token is None

    def test_both_token_and_certificate_token_precedence(
        self, canfar_client_fixture, tmp_path
    ) -> None:
        """Test that token takes precedence when both are provided."""
        cert_path = tmp_path / "test.pem"
        _create_test_certificate(cert_path)

        with patch("canfar.client.log") as mock_log:
            client = canfar_client_fixture(
                token=SecretStr("test-token"),
                certificate=cert_path,
                url="https://example.com",
            )

            # Token should be set, certificate should be None
            assert client.token.get_secret_value() == "test-token"
            assert client.certificate is None

            # Should log warnings about precedence
            mock_log.warning.assert_called()

    def test_token_without_url_raises_error(self, canfar_client_fixture) -> None:
        """Test that token without URL raises ValueError."""
        with pytest.raises(
            ValueError,
            match="Server URL must be provided when using runtime credentials",
        ):
            canfar_client_fixture(token=SecretStr("test-token"))

    def test_certificate_without_url_raises_error(
        self, canfar_client_fixture, tmp_path
    ) -> None:
        """Test that certificate without URL raises ValueError."""
        cert_path = tmp_path / "test.pem"
        _create_test_certificate(cert_path)

        with pytest.raises(
            ValueError,
            match="Server URL must be provided when using runtime credentials",
        ):
            canfar_client_fixture(certificate=cert_path)

    def test_invalid_certificate_path_raises_error(self, canfar_client_fixture) -> None:
        """Test that non-existent certificate path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            canfar_client_fixture(
                certificate=Path("/nonexistent/path.pem"), url="https://example.com"
            )

    def test_token_setup_headers(self, canfar_client_fixture) -> None:
        """Test token setup creates correct headers."""
        token = "abcdef"
        client = canfar_client_fixture(
            token=SecretStr(token), url="https://example.com"
        )
        assert client.token.get_secret_value() == token
        assert client.client.headers["Authorization"] == f"Bearer {token}"


def _create_test_certificate(
    path: Path, expired: bool = False, not_yet_valid: bool = False
) -> None:
    """Create a test certificate for testing purposes.

    Args:
        path: Path where to save the certificate
        expired: Whether to create an expired certificate
        not_yet_valid: Whether to create a certificate that's not yet valid
    """
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Create certificate
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Test"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test"),
            x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com"),
        ]
    )

    now = datetime.now(timezone.utc)
    if expired:
        not_valid_before = now - timedelta(days=365)
        not_valid_after = now - timedelta(days=1)
    elif not_yet_valid:
        not_valid_before = now + timedelta(days=1)
        not_valid_after = now + timedelta(days=365)
    else:
        not_valid_before = now - timedelta(days=1)
        not_valid_after = now + timedelta(days=365)

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before)
        .not_valid_after(not_valid_after)
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("test.example.com"),
                ]
            ),
            critical=False,
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    # Write certificate and private key to file
    with path.open("wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )


class TestBaseURLConstruction:
    """Test base URL construction based on precedence."""

    def test_runtime_url_precedence(self, canfar_client_fixture) -> None:
        """Test that runtime URL takes precedence."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://runtime.com/api"
        )
        base_url = client._get_base_url()
        assert str(base_url) == "https://runtime.com/api"

    def test_configured_url_from_context(self, canfar_client_fixture) -> None:
        """Test base URL construction from configuration context."""
        # Create a custom context with specific server settings
        custom_context = X509(
            path=Path("/test/cert.pem"),
            expiry=9999999999.0,
            server=Server(
                name="Test Server",
                uri=AnyUrl("ivo://test.org/canfar"),
                url=AnyHttpUrl("https://config.example.com"),
                version="v1",
            ),
        )

        config = Configuration(active="test", contexts={"test": custom_context})

        client = canfar_client_fixture(config=config)
        base_url = client._get_base_url()
        assert str(base_url) == "https://config.example.com//v1"

    def test_no_server_in_context_raises_error(self, canfar_client_fixture) -> None:
        """Test that missing server in context raises ValueError."""
        # Create a context without server
        custom_context = X509(
            path=Path("/test/cert.pem"), expiry=9999999999.0, server=None
        )

        config = Configuration(active="test", contexts={"test": custom_context})

        client = canfar_client_fixture(config=config)
        with pytest.raises(ValueError, match="Server not found in auth context"):
            client._get_base_url()


class TestCertificateValidation:
    """Test certificate validation functionality."""

    def test_certificate_validation_with_token_skips_validation(self, tmp_path) -> None:
        """Test certificate validation when token provided takes precedence."""
        # Create a valid certificate file for this test
        cert_path = tmp_path / "valid.pem"
        _create_test_certificate(cert_path)

        # Even with a valid certificate, when token is provided, it should use the token
        client = HTTPClient(
            token=SecretStr("test-token"),
            certificate=cert_path,
            url="https://example.com",
        )
        assert client.token is not None
        assert client.certificate is None  # Certificate should be nullified

        # Verify that the client uses token authentication
        headers = client._get_http_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["X-Skaha-Authentication-Type"] == "RUNTIME-TOKEN"

    def test_certificate_file_not_exists(self, tmp_path) -> None:
        """Test certificate validation when file doesn't exist."""
        cert_path = tmp_path / "nonexistent.pem"

        with pytest.raises(FileNotFoundError):
            HTTPClient(certificate=cert_path, url="https://example.com")

    def test_certificate_not_readable(self, tmp_path) -> None:
        """Test certificate validation when file is not readable."""
        cert_path = tmp_path / "test.pem"
        # Create a valid certificate file first
        _create_test_certificate(cert_path)

        # Mock the x509.inspect to raise PermissionError
        with (
            patch(
                "canfar.auth.x509.inspect",
                side_effect=PermissionError("Permission denied"),
            ),
            pytest.raises(PermissionError),
        ):
            HTTPClient(certificate=cert_path, url="https://example.com")

    def test_certificate_valid(self, tmp_path) -> None:
        """Test certificate validation with valid certificate."""
        cert_path = tmp_path / "valid.pem"
        _create_test_certificate(cert_path)

        # Should not raise an error
        client = HTTPClient(certificate=cert_path, url="https://example.com")
        assert client.certificate == cert_path


class TestHTTPClientCreationAndHeaders:
    """Test HTTP client creation and header generation."""

    def test_lazy_client_initialization(self, canfar_client_fixture) -> None:
        """Test that httpx clients are created only on first access."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com"
        )

        # Initially, private attributes should be None
        assert client._client is None
        assert client._asynclient is None

        # Access client property to trigger creation
        sync_client = client.client
        assert client._client is not None
        assert isinstance(sync_client, httpx.Client)

        # Access asynclient property to trigger creation
        async_client = client.asynclient
        assert client._asynclient is not None
        assert isinstance(async_client, httpx.AsyncClient)

    def test_default_headers_present(self, canfar_client_fixture) -> None:
        """Test that common headers are present."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com"
        )
        headers = client._get_http_headers()

        assert "Content-Type" in headers
        assert "Accept" in headers
        assert "User-Agent" in headers
        assert "Date" in headers
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert headers["Accept"] == "application/json"
        assert "python-canfar" in headers["User-Agent"]

    def test_runtime_token_headers(self, canfar_client_fixture) -> None:
        """Test headers for runtime token authentication."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com"
        )
        headers = client._get_http_headers()

        assert headers["Authorization"] == "Bearer test-token"
        assert headers["X-Skaha-Authentication-Type"] == "RUNTIME-TOKEN"

    def test_runtime_certificate_headers(self, canfar_client_fixture, tmp_path) -> None:
        """Test headers for runtime certificate authentication."""
        cert_path = tmp_path / "test.pem"
        _create_test_certificate(cert_path)

        client = canfar_client_fixture(certificate=cert_path, url="https://example.com")
        headers = client._get_http_headers()

        assert headers["X-Skaha-Authentication-Type"] == "RUNTIME-X509"
        assert "Authorization" not in headers

    def test_oidc_context_headers(self, canfar_client_fixture) -> None:
        """Test headers for OIDC context authentication."""
        # Create a real OIDC context
        oidc_context = OIDC(
            server=Server(
                name="Test OIDC",
                uri=AnyUrl("ivo://test.org/skaha"),
                url=AnyHttpUrl("https://oidc.example.com"),
                version="v1",
            ),
            endpoints=Endpoint(
                discovery="https://oidc.example.com/.well-known/openid-configuration",
                token="https://oidc.example.com/token",
            ),
            client=Client(identity="test-client", secret="test-secret"),
            token=Token(access="oidc-access-token", refresh="refresh-token"),
            expiry=Expiry(access=9999999999.0, refresh=9999999999.0),
        )

        config = Configuration(active="oidc", contexts={"oidc": oidc_context})

        client = canfar_client_fixture(config=config)
        headers = client._get_http_headers()

        assert headers["Authorization"] == "Bearer oidc-access-token"
        assert headers["X-Skaha-Authentication-Type"] == "OIDC"

    def test_x509_context_headers(self, canfar_client_fixture) -> None:
        """Test headers for X509 context authentication."""
        # Create a real X509 context
        x509_context = X509(
            path=Path("/test/cert.pem"),
            expiry=9999999999.0,
            server=Server(
                name="Test X509",
                uri=AnyUrl("ivo://test.org/skaha"),
                url=AnyHttpUrl("https://x509.example.com"),
                version="v1",
            ),
        )

        config = Configuration(active="x509", contexts={"x509": x509_context})

        client = canfar_client_fixture(config=config)
        headers = client._get_http_headers()

        assert headers["X-Skaha-Authentication-Type"] == "X509"
        assert "Authorization" not in headers

    def test_registry_headers(self, canfar_client_fixture) -> None:
        """Test headers with registry authentication."""
        registry = ContainerRegistry(username="test", secret="test")
        config = Configuration()
        config.registry = registry

        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com", config=config
        )
        headers = client._get_http_headers()

        assert "X-Skaha-Registry-Auth" in headers

    def test_client_kwargs_timeout_and_concurrency(self, canfar_client_fixture) -> None:
        """Test that httpx clients are initialized with correct timeout and limits."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"),
            url="https://example.com",
            timeout=45,
            concurrency=16,
        )

        # Test sync client kwargs
        sync_kwargs = client._get_client_kwargs(asynchronous=False)
        assert "timeout" in sync_kwargs
        # httpx.Timeout doesn't have a .timeout attribute, it's the object itself
        assert isinstance(sync_kwargs["timeout"], httpx.Timeout)
        assert "limits" not in sync_kwargs  # Only for async

        # Test async client kwargs
        async_kwargs = client._get_client_kwargs(asynchronous=True)
        assert "timeout" in async_kwargs
        assert isinstance(async_kwargs["timeout"], httpx.Timeout)
        assert "limits" in async_kwargs
        assert async_kwargs["limits"].max_connections == 16

    def test_oidc_refresh_hook_added(self, canfar_client_fixture) -> None:
        """Test that OIDC refresh hook is added for OIDC contexts."""
        # Create a real OIDC context
        oidc_context = OIDC(
            server=Server(
                name="Test OIDC",
                uri=AnyUrl("ivo://test.org/skaha"),
                url=AnyHttpUrl("https://oidc.example.com"),
                version="v1",
            ),
            endpoints=Endpoint(
                discovery="https://oidc.example.com/.well-known/openid-configuration",
                token="https://oidc.example.com/token",
            ),
            client=Client(identity="test-client", secret="test-secret"),
            token=Token(access="oidc-access-token", refresh="refresh-token"),
            expiry=Expiry(access=9999999999.0, refresh=9999999999.0),
        )

        config = Configuration(active="oidc", contexts={"oidc": oidc_context})

        client = canfar_client_fixture(config=config)

        # Test sync client kwargs
        sync_kwargs = client._get_client_kwargs(asynchronous=False)
        assert "event_hooks" in sync_kwargs
        assert "request" in sync_kwargs["event_hooks"]

        # Test async client kwargs
        async_kwargs = client._get_client_kwargs(asynchronous=True)
        assert "event_hooks" in async_kwargs
        assert "request" in async_kwargs["event_hooks"]


class TestContextManagerBehavior:
    """Test context manager functionality."""

    def test_sync_context_manager_enter_exit(self, canfar_client_fixture) -> None:
        """Test synchronous context manager entry and exit."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com"
        )

        # Test __enter__
        with client as ctx_client:
            assert ctx_client is client
            # Verify client is created
            assert isinstance(ctx_client.client, httpx.Client)

        # After exit, client should be closed
        assert client._client is None

    def test_sync_session_context(self, canfar_client_fixture) -> None:
        """Test synchronous session context manager."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com"
        )

        with client._session() as session:
            assert isinstance(session, httpx.Client)

        # After exit, client should be closed
        assert client._client is None

    def test_close_sync_client(self, canfar_client_fixture) -> None:
        """Test closing synchronous client."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com"
        )

        # Access client to create it
        _ = client.client
        assert client._client is not None

        # Close it
        client._close()
        assert client._client is None

    def test_close_sync_client_when_none(self, canfar_client_fixture) -> None:
        """Test closing synchronous client when it's None."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com"
        )

        # Don't access client, so it remains None
        assert client._client is None

        # Close should not raise an error
        client._close()
        assert client._client is None

    async def test_async_context_manager_enter_exit(
        self, canfar_client_fixture
    ) -> None:
        """Test asynchronous context manager entry and exit."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com"
        )

        # Test __aenter__
        async with client as ctx_client:
            assert ctx_client is client
            # Verify asynclient is created
            assert isinstance(ctx_client.asynclient, httpx.AsyncClient)

        # After exit, asynclient should be closed
        assert client._asynclient is None

    async def test_async_session_context(self, canfar_client_fixture) -> None:
        """Test asynchronous session context manager."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com"
        )

        async with client._asession() as session:
            assert isinstance(session, httpx.AsyncClient)

        # After exit, asynclient should be closed
        assert client._asynclient is None

    async def test_aclose_async_client(self, canfar_client_fixture) -> None:
        """Test closing asynchronous client."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com"
        )

        # Access asynclient to create it
        _ = client.asynclient
        assert client._asynclient is not None

        # Close it
        await client._aclose()
        assert client._asynclient is None

    async def test_aclose_async_client_when_none(self, canfar_client_fixture) -> None:
        """Test closing asynchronous client when it's None."""
        client = canfar_client_fixture(
            token=SecretStr("test-token"), url="https://example.com"
        )

        # Don't access asynclient, so it remains None
        assert client._asynclient is None

        # Close should not raise an error
        await client._aclose()
        assert client._asynclient is None


class TestSSLContextAndClientKwargs:
    """Test SSL context creation and client kwargs generation."""

    def test_get_client_kwargs_with_certificate(
        self, canfar_client_fixture, tmp_path
    ) -> None:
        """Test client kwargs with certificate authentication."""
        cert_path = tmp_path / "test.pem"
        _create_test_certificate(cert_path)

        client = canfar_client_fixture(certificate=cert_path, url="https://example.com")
        kwargs = client._get_client_kwargs(asynchronous=False)

        assert "verify" in kwargs
        assert isinstance(kwargs["verify"], ssl.SSLContext)

    def test_get_ssl_context_valid_certificate(
        self, canfar_client_fixture, tmp_path
    ) -> None:
        """Test SSL context creation with valid certificate."""
        cert_path = tmp_path / "test.pem"
        _create_test_certificate(cert_path)

        client = canfar_client_fixture(certificate=cert_path, url="https://example.com")
        ssl_context = client._get_ssl_context(cert_path)

        assert isinstance(ssl_context, ssl.SSLContext)
        assert ssl_context.minimum_version == ssl.TLSVersion.TLSv1_2


def test_non_readable_certfile() -> None:
    """Test non-readable certificate file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp_path = temp.name
    # Change the permissions
    Path(temp_path).chmod(0o000)
    with pytest.raises(PermissionError):
        HTTPClient(certificate=temp_path, url="https://example.com")
