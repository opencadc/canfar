"""Test CANFAR Python Client API."""

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
from pydantic import AnyUrl, SecretStr, ValidationError

from canfar.client import HTTPClient
from canfar.exceptions.context import AuthExpiredError
from canfar.models.auth import X509Credential
from canfar.models.config import Configuration
from canfar.models.http import Server
from canfar.models.registry import ContainerRegistry
from tests.helpers.config import configuration_with_credential, oidc_config, x509_config
from tests.test_auth_x509 import generate_cert


# Test Fixtures
@pytest.fixture
def canfar_client_fixture():
    """Fixture that yields a HTTPClient instance for testing."""

    def _create_client(**kwargs):
        return HTTPClient(**kwargs)

    return _create_client


def _sync_client_factory(transport: httpx.BaseTransport):
    """Build native sync HTTPX clients over a supplied transport."""
    return lambda **kwargs: httpx.Client(transport=transport, **kwargs)


def _async_client_factory(transport: httpx.BaseTransport):
    """Build native async HTTPX clients over a supplied transport."""
    return lambda **kwargs: httpx.AsyncClient(transport=transport, **kwargs)


def _response_transport(requests: list[httpx.Request]) -> httpx.MockTransport:
    """Record requests and return one successful native HTTPX response."""

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True}, request=request)

    return httpx.MockTransport(respond)


class TestInitializationAndConfiguration:
    """Test HTTPClient initialization and configuration loading."""

    def test_default_initialization(self, canfar_client_fixture) -> None:
        """Test default initialization with no arguments."""
        client = canfar_client_fixture()
        assert client.timeout == 30
        assert client.concurrency == 32
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
        )
        assert client.timeout == 60
        assert client.concurrency == 64
        assert client.token.get_secret_value() == "test-token"
        # Certificate should be None due to token precedence
        assert client.certificate is None
        assert str(client.url) == "https://example.com/api"
        assert client.config is config

    def test_environment_variables(self, canfar_client_fixture, monkeypatch) -> None:
        """Test that environment variables are picked up correctly."""
        monkeypatch.setenv("CANFAR_TIMEOUT", "45")
        monkeypatch.setenv("CANFAR_CONCURRENCY", "16")
        monkeypatch.setenv("CANFAR_TOKEN", "env-token")
        monkeypatch.setenv("CANFAR_URL", "https://env.example.com")

        client = canfar_client_fixture()
        assert client.timeout == 45
        assert client.concurrency == 16
        assert client.token.get_secret_value() == "env-token"
        # URL gets normalized with trailing slash
        assert str(client.url) == "https://env.example.com/"

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

    def test_empty_token_uses_saved_oidc_authentication(
        self,
        canfar_client_fixture,
    ) -> None:
        """A sync request uses saved OIDC state when the runtime token is empty."""
        config = oidc_config(idp="oidc")
        requests: list[httpx.Request] = []

        with (
            patch(
                "canfar.client.Client",
                side_effect=_sync_client_factory(_response_transport(requests)),
            ),
            canfar_client_fixture(config=config, token=SecretStr("")) as client,
        ):
            assert not client.uses_runtime_credentials
            response = client.client.get("probe")

        assert response.json() == {"ok": True}
        assert len(requests) == 1
        request = requests[0]
        assert str(request.url) == "https://oidc.example.com//v1/probe"
        assert request.headers["Authorization"] == "Bearer access-token"
        assert request.headers["X-Skaha-Authentication-Type"] == "OIDC"

    async def test_empty_token_uses_saved_oidc_authentication_async(
        self,
        canfar_client_fixture,
    ) -> None:
        """An async request uses saved OIDC state when the runtime token is empty."""
        requests: list[httpx.Request] = []

        with patch(
            "canfar.client.AsyncClient",
            side_effect=_async_client_factory(_response_transport(requests)),
        ):
            async with canfar_client_fixture(
                config=oidc_config(idp="oidc"),
                token=SecretStr(""),
            ) as client:
                response = await client.asynclient.get("probe")

        assert response.json() == {"ok": True}
        assert len(requests) == 1
        request = requests[0]
        assert str(request.url) == "https://oidc.example.com//v1/probe"
        assert request.headers["Authorization"] == "Bearer access-token"
        assert request.headers["X-Skaha-Authentication-Type"] == "OIDC"

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
        """A request uses the runtime URL when runtime credentials are supplied."""
        requests: list[httpx.Request] = []

        with (
            patch(
                "canfar.client.Client",
                side_effect=_sync_client_factory(_response_transport(requests)),
            ),
            canfar_client_fixture(
                token=SecretStr("test-token"), url="https://runtime.com/api"
            ) as client,
        ):
            response = client.client.get("probe")

        assert response.status_code == 200
        assert str(requests[0].url) == "https://runtime.com/api/probe"
        assert requests[0].headers["Authorization"] == "Bearer test-token"

    def test_configured_url_from_context(self, canfar_client_fixture) -> None:
        """A request uses the configured Science Platform Server URL."""
        requests: list[httpx.Request] = []

        with (
            patch(
                "canfar.client.Client",
                side_effect=_sync_client_factory(_response_transport(requests)),
            ),
            canfar_client_fixture(
                config=oidc_config(server_url="https://config.example.com")
            ) as client,
        ):
            response = client.client.get("probe")

        assert response.status_code == 200
        assert str(requests[0].url) == "https://config.example.com//v1/probe"

    def test_no_server_in_context_raises_error(self, canfar_client_fixture) -> None:
        """Test that missing server in context raises ValueError."""
        config = configuration_with_credential(
            X509Credential(
                idp="test", path=Path("/test/cert.pem"), expiry=9999999999.0
            ),
        )

        with (
            canfar_client_fixture(config=config) as client,
            pytest.raises(
                ValueError, match="Server not found for Authentication Record"
            ),
        ):
            client.client.get("probe")

    def test_active_server_without_url_raises_error(
        self, canfar_client_fixture
    ) -> None:
        """Test that active server with no URL raises ValueError."""
        config = configuration_with_credential(
            X509Credential(
                idp="test", path=Path("/test/cert.pem"), expiry=9999999999.0
            ),
            server=Server(
                name="TestServer",
                uri=AnyUrl("ivo://test.org/canfar"),
                version="v1",
            ),
        )

        with (
            canfar_client_fixture(config=config) as client,
            pytest.raises(ValueError, match="Active server has no URL configured"),
        ):
            client.client.get("probe")


class TestCertificateValidation:
    """Test certificate validation functionality."""

    def test_certificate_validation_with_token_skips_validation(self, tmp_path) -> None:
        """A runtime-token request ignores a supplied certificate."""
        # Create a valid certificate file for this test
        cert_path = tmp_path / "valid.pem"
        _create_test_certificate(cert_path)

        requests: list[httpx.Request] = []
        with (
            patch(
                "canfar.client.Client",
                side_effect=_sync_client_factory(_response_transport(requests)),
            ),
            HTTPClient(
                token=SecretStr("test-token"),
                certificate=cert_path,
                url="https://example.com",
            ) as client,
        ):
            response = client.client.get("probe")

        assert response.status_code == 200
        assert len(requests) == 1
        assert str(requests[0].url) == "https://example.com/probe"
        assert requests[0].headers["Authorization"] == "Bearer test-token"
        assert requests[0].headers["X-Skaha-Authentication-Type"] == "RUNTIME-TOKEN"

    def test_certificate_validates_for_native_request(self, tmp_path) -> None:
        """A valid certificate can build a native client and complete a request."""
        cert_path = tmp_path / "valid.pem"
        _create_test_certificate(cert_path)
        requests: list[httpx.Request] = []

        with (
            patch(
                "canfar.client.Client",
                side_effect=_sync_client_factory(_response_transport(requests)),
            ),
            HTTPClient(certificate=cert_path, url="https://example.com") as client,
        ):
            response = client.client.get("probe")

        assert response.status_code == 200
        assert len(requests) == 1
        assert requests[0].headers["X-Skaha-Authentication-Type"] == "RUNTIME-X509"

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


class TestHTTPClientCreationAndHeaders:
    """Test HTTP client requests and header generation."""

    def test_sync_request_includes_common_and_registry_headers(
        self,
    ) -> None:
        """A native sync request carries common and registry headers."""
        config = Configuration()
        config.registry = ContainerRegistry(username="test", secret="test")
        requests: list[httpx.Request] = []

        with (
            patch(
                "canfar.client.formatdate",
                return_value="Wed, 09 Jun 2026 12:00:00 GMT",
            ) as mock_formatdate,
            patch(
                "canfar.client.Client",
                side_effect=_sync_client_factory(_response_transport(requests)),
            ),
            HTTPClient(
                token=SecretStr("test-token"),
                url="https://example.com",
                config=config,
            ) as client,
        ):
            response = client.client.get("probe")

        assert response.status_code == 200
        mock_formatdate.assert_called_once_with(usegmt=True)
        request = requests[0]
        assert str(request.url) == "https://example.com/probe"
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["X-Skaha-Authentication-Type"] == "RUNTIME-TOKEN"
        assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert request.headers["Accept"] == "application/json"
        assert request.headers["Date"] == "Wed, 09 Jun 2026 12:00:00 GMT"
        assert "python-canfar" in request.headers["User-Agent"]
        assert request.headers["X-Skaha-Registry-Auth"] == "dGVzdDp0ZXN0"

    async def test_async_request_includes_common_headers(
        self,
        canfar_client_fixture,
    ) -> None:
        """A native async request carries common headers and returns its result."""
        requests: list[httpx.Request] = []

        with (
            patch(
                "canfar.client.AsyncClient",
                side_effect=_async_client_factory(_response_transport(requests)),
            ),
            canfar_client_fixture(
                token=SecretStr("test-token"), url="https://example.com"
            ) as client,
        ):
            response = await client.asynclient.get("probe")

        assert response.status_code == 200
        assert len(requests) == 1
        request = requests[0]
        assert str(request.url) == "https://example.com/probe"
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["X-Skaha-Authentication-Type"] == "RUNTIME-TOKEN"
        assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert request.headers["Accept"] == "application/json"


class TestContextManagerBehavior:
    """Test context manager functionality."""

    def test_sync_context_manager_enter_exit(self, canfar_client_fixture) -> None:
        """The sync context manager returns the client and closes HTTPX."""
        requests: list[httpx.Request] = []
        created: list[httpx.Client] = []

        def factory(**kwargs: object) -> httpx.Client:
            native = httpx.Client(transport=_response_transport(requests), **kwargs)
            created.append(native)
            return native

        with (
            patch("canfar.client.Client", side_effect=factory),
            canfar_client_fixture(
                token=SecretStr("test-token"), url="https://example.com"
            ) as client,
        ):
            response = client.client.get("probe")

        assert response.status_code == 200
        assert len(requests) == 1
        assert created[0].is_closed

    async def test_async_context_manager_enter_exit(
        self, canfar_client_fixture
    ) -> None:
        """The async context manager returns the client and closes HTTPX."""
        requests: list[httpx.Request] = []
        created: list[httpx.AsyncClient] = []

        def factory(**kwargs: object) -> httpx.AsyncClient:
            native = httpx.AsyncClient(
                transport=_response_transport(requests), **kwargs
            )
            created.append(native)
            return native

        with patch("canfar.client.AsyncClient", side_effect=factory):
            async with canfar_client_fixture(
                token=SecretStr("test-token"), url="https://example.com"
            ) as client:
                response = await client.asynclient.get("probe")

        assert response.status_code == 200
        assert len(requests) == 1
        assert created[0].is_closed


class TestSSLContextAndClientKwargs:
    """Test observable TLS validation and request-hook behavior."""

    def test_expiry_hook_omitted_for_runtime_token(
        self, canfar_client_fixture, tmp_path
    ) -> None:
        """Runtime credentials bypass expiry checks from saved X.509 state."""
        cert_path = tmp_path / "expired.pem"
        generate_cert(cert_path, expired=True)
        requests: list[httpx.Request] = []
        config = x509_config(idp="x509", path=cert_path, expiry=0.0)

        with (
            patch(
                "canfar.client.Client",
                side_effect=_sync_client_factory(_response_transport(requests)),
            ),
            canfar_client_fixture(
                config=config,
                token=SecretStr("runtime-token"),
                url="https://runtime.com",
            ) as client,
        ):
            response = client.client.get("probe")

        assert response.status_code == 200
        assert len(requests) == 1
        assert requests[0].headers["Authorization"] == "Bearer runtime-token"

    async def test_async_expiry_hook_omitted_for_runtime_token(
        self, canfar_client_fixture, tmp_path
    ) -> None:
        """Async runtime credentials bypass saved X.509 expiry checks."""
        cert_path = tmp_path / "expired.pem"
        generate_cert(cert_path, expired=True)
        requests: list[httpx.Request] = []

        with patch(
            "canfar.client.AsyncClient",
            side_effect=_async_client_factory(_response_transport(requests)),
        ):
            async with canfar_client_fixture(
                config=x509_config(idp="x509", path=cert_path, expiry=0.0),
                token=SecretStr("runtime-token"),
                url="https://runtime.com",
            ) as client:
                response = await client.asynclient.get("probe")

        assert response.status_code == 200
        assert len(requests) == 1
        assert requests[0].headers["Authorization"] == "Bearer runtime-token"

    def test_expiry_hook_present_for_saved_expired_x509(
        self, canfar_client_fixture, tmp_path
    ) -> None:
        """A sync request rejects an expired saved X.509 record."""
        cert_path = tmp_path / "expired.pem"
        generate_cert(cert_path, expired=True)
        requests: list[httpx.Request] = []
        config = x509_config(idp="x509", path=cert_path, expiry=0.0)

        with (
            patch(
                "canfar.client.Client",
                side_effect=_sync_client_factory(_response_transport(requests)),
            ),
            canfar_client_fixture(config=config) as client,
            pytest.raises(AuthExpiredError, match="expired"),
        ):
            client.client.get("probe")

        assert requests == []

    async def test_async_expiry_hook_present_for_saved_expired_x509(
        self, canfar_client_fixture, tmp_path
    ) -> None:
        """An async request rejects an expired saved X.509 record."""
        cert_path = tmp_path / "expired.pem"
        generate_cert(cert_path, expired=True)
        requests: list[httpx.Request] = []

        with (
            patch(
                "canfar.client.AsyncClient",
                side_effect=_async_client_factory(_response_transport(requests)),
            ),
            pytest.raises(AuthExpiredError, match="expired"),
        ):
            async with canfar_client_fixture(
                config=x509_config(idp="x509", path=cert_path, expiry=0.0)
            ) as client:
                await client.asynclient.get("probe")

        assert requests == []


def test_non_readable_certfile() -> None:
    """Test non-readable certificate file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp_path = temp.name
    # Change the permissions
    Path(temp_path).chmod(0o000)
    with pytest.raises(PermissionError):
        HTTPClient(certificate=temp_path, url="https://example.com")
