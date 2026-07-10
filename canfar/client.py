"""HTTP Client Composition for CANFAR Science Platform."""

from __future__ import annotations

import ssl
from datetime import datetime, timezone
from email.utils import formatdate
from pathlib import Path
from typing import TYPE_CHECKING, Any

from httpx import URL, AsyncClient, Client, Limits, Timeout
from pydantic import (
    AnyHttpUrl,
    Field,
    PrivateAttr,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

from canfar import __version__, get_logger
from canfar.auth import x509
from canfar.exceptions.context import AuthContextError
from canfar.hooks.httpx import auth, errors, expiry
from canfar.models.auth import (
    AuthenticationCredential,
    OIDCCredential,
    X509Credential,
)
from canfar.models.config import Configuration

if TYPE_CHECKING:
    from types import TracebackType

log = get_logger(__name__)


class HTTPClient(BaseSettings):
    """HTTP Client for interacting with CANFAR Science Platform services (V2).

    This client uses a composition-based approach and inherits from Pydantic's
    BaseSettings to allow for flexible configuration via arguments, environment
    variables, or a configuration file.

    The client prioritizes credentials in the following order:

    1.  **Runtime Arguments/Environment Variables**: A `token` or `certificate`
        provided at instantiation (e.g., `CANFAR_TOKEN="..."`).
    2.  **Saved Authentication**: The Authentication Record named by transient
        ``authentication_idp`` or ``active.authentication``, plus the active Server
        Selection when no explicit ``url`` is supplied.

    Raises:
        ValueError: If configuration is invalid.
    """

    model_config = SettingsConfigDict(
        title="CANFAR Client V2",
        env_prefix="CANFAR_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",  # Allow extra fields for config composition
    )

    # Runtime/environment variable settings
    token: SecretStr | None = Field(
        None,
        title="Runtime Authentication Token",
        description="Bearer token for runtime authentication.",
        examples=["your-bearer-token-here"],
        exclude=True,
    )
    certificate: Path | None = Field(
        None,
        title="Runtime X.509 Certificate",
        description="Path to a runtime x509 certificate file.",
        examples=[Path.home() / ".ssl" / "cadcproxy.pem"],
    )
    url: AnyHttpUrl | None = Field(
        None,
        title="Server URL",
        description="The server URL for runtime credentials.",
        examples=["https://ws-uv.canfar.net/server/v0/"],
    )
    authentication_idp: str | None = Field(
        default=None,
        title="Transient Authentication IDP",
        description=(
            "Optional Authentication Record selector for this client only; "
            "does not change persisted Authentication or Server Selection."
        ),
        exclude=True,
    )
    timeout: int = Field(
        30,
        title="HTTP Timeout",
        description="HTTP request timeout in seconds.",
        gt=0,
        le=300,
    )
    concurrency: int = Field(
        32,
        title="HTTP Concurrency",
        description="Max concurrent connections for async client.",
        ge=1,
        le=128,
    )
    raise_http_errors: bool = Field(
        default=True,
        title="Raise HTTP Errors",
        description="Install response hooks that raise HTTP status errors.",
        exclude=True,
    )
    loglevel: int | str = Field(
        default="INFO",
        title="Logging level for the client.",
        description="10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL",
        examples=["info", "10"],
        validate_default=False,
    )

    # Composed configuration object
    config: Configuration = Field(
        default_factory=Configuration,
        title="Configuration Object",
        description="The configuration object for the client.",
    )

    # Private attributes
    _client: Client | None = PrivateAttr(default=None)
    _asynclient: AsyncClient | None = PrivateAttr(default=None)

    # Client Properties
    @property
    def client(self) -> Client:
        """Get the synchronous HTTPx Client.

        Returns:
            Client: The synchronous HTTPx client.
        """
        if not self._client:
            self._client = self._create_sync_client()
            log.debug("Synchronous HTTPx client created")
        return self._client

    @property
    def asynclient(self) -> AsyncClient:
        """Get the asynchronous HTTPx Async Client."""
        if not self._asynclient:
            self._asynclient = self._create_async_client()
            log.debug("Asynchronous HTTPx client created")
        return self._asynclient

    @property
    def uses_runtime_credentials(self) -> bool:
        """Return whether runtime token or certificate credentials are active."""
        return bool(self.token or self.certificate)

    @property
    def authentication_record(self) -> AuthenticationCredential | None:
        """Return this client's selected usable Authentication Record, if any."""
        idp = (
            self.config.active.authentication
            if self.authentication_idp is None
            else self.authentication_idp
        )
        try:
            credential = self.config.get_credential(idp)
        except KeyError:
            return None
        if isinstance(credential, X509Credential) and credential.path is None:
            return None
        return credential

    @field_validator("loglevel", mode="before")
    @classmethod
    def _validate_loglevel(cls, value: int | str) -> str:
        """Validate and set the log level.

        Args:
            value (int | str): Log level as an integer or string.

        Returns:
            str: Log level as a string.
        """
        valid: dict[int, str] = {
            0: "NOTSET",
            10: "DEBUG",
            20: "INFO",
            30: "WARNING",
            40: "ERROR",
            50: "CRITICAL",
        }
        if isinstance(value, int):
            value = valid[value]
        value = value.upper()
        assert value in valid.values(), f"Invalid log level: {value}"
        return value

    @model_validator(mode="after")
    def _validate(self) -> Self:
        """Configure the client based on the provided settings.

        Raises:
            ValueError: If the configuration is invalid.

        Returns:
            Self: The configured client.
        """
        if self.token and self.certificate:
            log.warning("Both runtime token and certificate values provided.")
            log.warning("Runtime token takes precedence over certificate.")
            log.warning("Certificate will be ignored in favor of the token.")
            self.certificate = None  # Nullify certificate to ensure token is used

        if (self.token or self.certificate) and not self.url:
            msg = "Server URL must be provided when using runtime credentials."
            raise ValueError(msg)

        if self.certificate:
            info = x509.inspect(self.certificate)
            expiry = datetime.fromtimestamp(info["expiry"], tz=timezone.utc).isoformat()
            msg = f"{self.certificate} valid till {expiry}"
            log.debug(msg)

        return self

    def _create_async_client(self) -> AsyncClient:
        """Create an asynchronous HTTPx client.

        Returns:
            AsyncClient: The asynchronous HTTPx client.
        """
        kwargs = self._get_client_kwargs(asynchronous=True)
        log.debug("HTTPx async client kwargs: %s", kwargs)
        headers = self._get_http_headers()
        client = AsyncClient(**kwargs)
        client.headers.update(headers)
        return client

    def _create_sync_client(self) -> Client:
        """Create a synchronous HTTPx client.

        Returns:
            Client: The synchronous HTTPx client.
        """
        kwargs = self._get_client_kwargs(asynchronous=False)
        log.debug("HTTPx sync client kwargs: %s", kwargs)
        headers = self._get_http_headers()
        client = Client(**kwargs)
        client.headers.update(headers)
        return client

    def _get_base_url(self) -> URL:
        """Get the base URL for the client.

        Returns:
            URL: The base URL for the client.
        """
        if self.url:
            return URL(str(self.url))
        try:
            server = self.config.get_active_server()
        except KeyError as exc:
            msg = (
                f"Server not found in auth context: {self.config.active.authentication}"
            )
            raise ValueError(msg) from exc
        if server.url is None:
            msg = f"Server not found in auth context: {server}"
            raise ValueError(msg)
        return URL(f"{server.url}/{server.version}")

    def _get_client_kwargs(self, asynchronous: bool) -> dict[str, Any]:
        """Get the keyword arguments for creating an HTTPx client.

        Args:
            asynchronous (bool): Whether the client is asynchronous.

        Returns:
            dict[str, Any]: Keyword arguments for creating an HTTPx client.
        """
        catcher = errors.acatch if asynchronous else errors.catch
        response_hooks = [catcher] if self.raise_http_errors else []
        request_hooks: list[Any] = []
        credential: AuthenticationCredential | None = None
        if not self.uses_runtime_credentials:
            credential = self.authentication_record
        if credential is not None:
            checker = expiry.acheck(self) if asynchronous else expiry.check(self)
            request_hooks.append(checker)
        kwargs: dict[str, Any] = {
            "timeout": Timeout(self.timeout),
            "event_hooks": {"request": request_hooks, "response": response_hooks},
            "base_url": self._get_base_url(),
        }
        # Configure connection pooling for async clients
        if asynchronous:
            kwargs["limits"] = Limits(
                max_connections=self.concurrency,
                max_keepalive_connections=self.concurrency // 4,
            )
        # Prioritize user-provided credentials over configuration
        if self.token:
            return kwargs

        if self.certificate:
            msg = "creating runtime ssl context with: {self.certificate}"
            log.debug(msg)
            kwargs["verify"] = self._get_ssl_context(self.certificate)
            return kwargs

        # No user-provided credentials, use the saved Authentication Record.
        # Note: The refresh hook must be the first request hook to run, since it may
        #       update the record and headers. The expiry hook then checks the
        #       updated record.
        if isinstance(credential, OIDCCredential):
            if not credential.valid:
                raise AuthContextError(
                    credential.idp,
                    "OIDC Authentication Record cannot refresh tokens.",
                )
            refresher = auth.arefresh(self) if asynchronous else auth.refresh(self)
            kwargs["event_hooks"]["request"].insert(0, refresher)
            return kwargs

        if isinstance(credential, X509Credential):
            if credential.path is None:
                raise AuthContextError(
                    credential.idp,
                    "X.509 certificate path is missing.",
                )
            try:
                x509.valid(credential.path)
                kwargs["verify"] = self._get_ssl_context(credential.path)
            except (OSError, ValueError) as err:
                raise AuthContextError(
                    credential.idp,
                    "X.509 certificate cannot be used.",
                ) from err
            return kwargs
        return kwargs

    def _get_ssl_context(self, source: Path) -> ssl.SSLContext:
        """Get SSL context from certificate file.

        Args:
            source (Path): Path to the certificate file.

        Returns:
            ssl.SSLContext: SSL context.
        """
        certfile = source.as_posix()
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(certfile=certfile)
        return ctx

    def _get_http_headers(self) -> dict[str, str]:
        """Generate HTTP headers for the client based on authentication mode.

        Returns:
            dict[str, str]: HTTP headers.
        """
        headers: dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Date": formatdate(usegmt=True),
            "User-Agent": f"python-canfar/{__version__}",
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token.get_secret_value()}"
            headers["X-Skaha-Authentication-Type"] = "RUNTIME-TOKEN"
        elif self.certificate:
            headers["X-Skaha-Authentication-Type"] = "RUNTIME-X509"
        else:
            credential = self.authentication_record
            if isinstance(credential, OIDCCredential):
                if not credential.valid:
                    raise AuthContextError(
                        credential.idp,
                        "OIDC Authentication Record cannot refresh tokens.",
                    )
                if credential.token.access is not None:
                    headers["Authorization"] = (
                        f"Bearer {credential.token.access.get_secret_value()}"
                    )
                elif not credential.refreshable:
                    raise AuthContextError(
                        credential.idp,
                        "OIDC Authentication Record has no usable access token.",
                    )
                headers["X-Skaha-Authentication-Type"] = "OIDC"
            elif isinstance(credential, X509Credential):
                headers["X-Skaha-Authentication-Type"] = "X509"
        # Add container registry authentication if configured
        if self.config.registry.username:
            headers["X-Skaha-Registry-Auth"] = self.config.registry.encoded()

        return headers

    # Context Manager Methods
    def __enter__(self) -> Self:
        """Sync context manager entry."""
        log.debug("Entering synchronous context manager")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Sync context manager exit."""
        log.debug("Exiting synchronous context manager")
        self._close()

    def _close(self) -> None:
        """Close sync client."""
        if self._client:
            log.debug("Closing synchronous HTTPx client")
            self._client.close()
            self._client = None
            log.debug("Synchronous HTTPx client closed")
        else:
            log.debug("No synchronous client to close")

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        log.debug("Entering asynchronous context manager")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        log.debug("Exiting asynchronous context manager")
        await self._aclose()

    async def _aclose(self) -> None:
        """Close async client."""
        if self._asynclient:
            log.debug("Closing asynchronous HTTPx client")
            await self._asynclient.aclose()
            self._asynclient = None
            log.debug("Asynchronous HTTPx client closed")
        else:
            log.debug("No asynchronous client to close")
