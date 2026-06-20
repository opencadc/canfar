"""Client HTTP Models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
from pydantic import AnyHttpUrl, AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from canfar.utils import vosi

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from canfar.models.config import Configuration
    from canfar.utils.vosi import Capability

DEFAULT_SERVER_CORES = 2
"""Default CPU core limit when context enrichment is unavailable."""

DEFAULT_SERVER_RAM_GB = 16
"""Default RAM limit in GB when context enrichment is unavailable."""

DEFAULT_SERVER_GPUS = 0
"""Default GPU count when context enrichment is unavailable."""


class Server(BaseSettings):
    """Science Platform Server Details."""

    model_config = SettingsConfigDict(
        title="CANFAR Client Server Configuration",
        env_prefix="CANFAR_SERVER_",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        json_schema_mode_override="serialization",
        str_strip_whitespace=True,
        str_max_length=256,
        str_min_length=1,
    )

    name: str | None = Field(
        default=None,
        title="Server Name",
        description="Common name for the science platform server.",
        examples=["SRCnet-Sweden", "SRCnet-UK-CAM"],
        min_length=1,
        max_length=256,
        validate_default=False,
    )
    uri: AnyUrl | None = Field(
        default=None,
        title="Server URI identifier",
        description="IVOA static uri identifier for the server.",
        examples=["ivo://swesrc.chalmers.se/skaha", "ivo://canfar.cam.uksrc.org/skaha"],
    )
    url: AnyHttpUrl | None = Field(
        default=None,
        title="Server URL",
        description="URL where the server is currently accessible from.",
        examples=[
            "https://services.swesrc.chalmers.se/skaha",
            "https://canfar.cam.uksrc.org/skaha",
        ],
    )
    version: str | None = Field(
        default=None,
        title="API Version",
        description="Server API Version.",
        pattern=r"^v\d+$",
        examples=["v0", "v1", "v2"],
        min_length=2,
        max_length=8,
    )
    auths: list[str] | None = Field(
        default=None,
        title="Supported Auth Modes",
        description="Authentication modes supported by the Server",
        examples=["oidc", "token", "x509"],
    )
    idp: str | None = Field(
        default=None,
        title="Identity Provider Key",
        description="Canonical IDP key this server belongs to.",
        min_length=1,
        max_length=64,
    )
    cores: int = Field(
        default=DEFAULT_SERVER_CORES,
        title="Default CPU Core Limit",
        description="Default maximum CPU cores available for session creation.",
        ge=1,
    )
    ram: int = Field(
        default=DEFAULT_SERVER_RAM_GB,
        title="Default RAM Limit (GB)",
        description="Default maximum RAM in gigabytes for session creation.",
        ge=1,
    )
    gpus: int = Field(
        default=DEFAULT_SERVER_GPUS,
        title="Maximum GPU Count",
        description="Maximum GPUs available for session creation.",
        ge=0,
    )
    status: str | None = Field(
        default=None,
        title="Discovery Reachability Status",
        description=(
            "Runtime-only discovery reachability status when known; "
            "not persisted in client configuration."
        ),
    )

    def capabilities(self, *, timeout: int | None = None) -> list[Capability]:
        """Fetch and parse the server's VOSI capabilities.

        Args:
            timeout: HTTP timeout in seconds.

        Returns:
            list[Capability]: Parsed session capability families for the server.
        """
        return vosi.capabilities(url=f"{self.url}/capabilities", timeout=timeout)

    def fetch(
        self,
        *,
        timeout: int | None = None,
        config: Configuration | None = None,
    ) -> Server:
        """Fetch server resource settings using active persisted authentication.

        Args:
            timeout: HTTP timeout in seconds.
            config: Configuration whose active Authentication and Server
                Selection should authenticate the context request.

        Returns:
            Server: New model populated with resource settings from the context
            endpoint, or default resource settings when the context endpoint
            cannot be retrieved.

        Raises:
            ValueError: If URL or version is missing.
        """
        return self._fetch_sync(timeout=timeout, config=config)

    async def afetch(
        self,
        *,
        timeout: int | None = None,
        config: Configuration | None = None,
    ) -> Server:
        """Asynchronously fetch server resource settings using active auth.

        Args:
            timeout: HTTP timeout in seconds.
            config: Configuration whose active Authentication and Server
                Selection should authenticate the context request.

        Returns:
            Server: New model populated with resource settings from the context
            endpoint, or default resource settings when the context endpoint
            cannot be retrieved.

        Raises:
            ValueError: If URL or version is missing.
        """
        return await self._fetch_async(timeout=timeout, config=config)

    def _fetch_sync(
        self,
        *,
        timeout: int | None = None,
        config: Configuration | None = None,
    ) -> Server:
        from canfar.client import HTTPClient  # noqa: PLC0415
        from canfar.models.config import Configuration  # noqa: PLC0415

        base_url = self._require_fetch_base_url()
        runtime_config = config or Configuration()  # ty: ignore[missing-argument]
        if timeout is None:
            client = HTTPClient(
                config=runtime_config,
                url=AnyHttpUrl(base_url),
                raise_http_errors=False,
            )
        else:
            client = HTTPClient(
                config=runtime_config,
                url=AnyHttpUrl(base_url),
                timeout=timeout,
                raise_http_errors=False,
            )
        try:
            response = client.client.get("context")
            response.raise_for_status()
            return self._from_context(dict(response.json()))
        except (httpx.HTTPError, OSError, ValueError, TypeError):
            return self.with_resource_defaults()

    async def _fetch_async(
        self,
        *,
        timeout: int | None = None,
        config: Configuration | None = None,
    ) -> Server:
        from canfar.client import HTTPClient  # noqa: PLC0415
        from canfar.models.config import Configuration  # noqa: PLC0415

        base_url = self._require_fetch_base_url()
        runtime_config = config or Configuration()  # ty: ignore[missing-argument]
        if timeout is None:
            client = HTTPClient(
                config=runtime_config,
                url=AnyHttpUrl(base_url),
                raise_http_errors=False,
            )
        else:
            client = HTTPClient(
                config=runtime_config,
                url=AnyHttpUrl(base_url),
                timeout=timeout,
                raise_http_errors=False,
            )
        try:
            response = await client.asynclient.get("context")
            response.raise_for_status()
            return self._from_context(dict(response.json()))
        except (httpx.HTTPError, OSError, ValueError, TypeError):
            return self.with_resource_defaults()

    def _require_fetch_base_url(self) -> str:
        """Return the API base URL required for context fetch.

        Returns:
            str: ``{url}/{version}`` base URL for the server API.

        Raises:
            ValueError: If URL or version is missing.
        """
        if self.url is None or self.version is None:
            msg = "Server URL and version are required for fetch."
            raise ValueError(msg)
        return f"{self.url}/{self.version}"

    @classmethod
    def _resource_settings_from_context(cls, data: dict[str, Any]) -> dict[str, int]:
        """Extract typed resource settings from a context API payload.

        Args:
            data: Parsed JSON body from the context endpoint.

        Returns:
            Mapping of ``cores``, ``ram``, and ``gpus`` resource settings.
        """
        cores_data = data.get("cores") or {}
        ram_data = data.get("memoryGB") or {}
        gpus_data = data.get("gpus") or {}

        cores = cores_data.get("defaultLimit")
        ram = ram_data.get("defaultLimit")
        gpu_options = gpus_data.get("options") or []
        gpus = max(gpu_options) if gpu_options else None

        return {
            "cores": cores if cores is not None else DEFAULT_SERVER_CORES,
            "ram": ram if ram is not None else DEFAULT_SERVER_RAM_GB,
            "gpus": gpus if gpus is not None else DEFAULT_SERVER_GPUS,
        }

    def with_resource_defaults(self) -> Server:
        """Return a copy with default resource settings applied.

        Returns:
            Server: Copy using default ``cores``, ``ram``, and ``gpus`` values.
        """
        return self.model_copy(
            update={
                "cores": DEFAULT_SERVER_CORES,
                "ram": DEFAULT_SERVER_RAM_GB,
                "gpus": DEFAULT_SERVER_GPUS,
            },
            deep=True,
        )

    def _from_context(self, data: dict[str, Any]) -> Server:
        """Build a new server model from a context API payload.

        Args:
            data: Parsed JSON body from the context endpoint.

        Returns:
            Server: Copy of this server with typed resource fields populated.
        """
        return self.model_copy(
            update=self._resource_settings_from_context(data),
            deep=True,
        )


class Connection(BaseSettings):
    """CANFAR Client HTTP Connection Details."""

    model_config = SettingsConfigDict(
        title="Science Platform Client Server Configuration",
        env_prefix="CANFAR_CONNECTION_",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        json_schema_mode_override="serialization",
        str_strip_whitespace=True,
        str_max_length=256,
        str_min_length=1,
    )

    concurrency: int = Field(
        default=32,
        title="HTTP Concurrency",
        description="Maximum concurrent http requests.",
        le=256,
        ge=1,
    )
    timeout: int = Field(
        default=30,
        title="HTTP Timeout",
        description="HTTP timeout in seconds.",
        gt=0,
        le=300,
    )
