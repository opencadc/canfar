"""CANFAR Client Configuration - v1."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Callable, Literal

import yaml
from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)
from pydantic_settings.sources import EnvSettingsSource

from canfar import CONFIG_PATH, get_logger
from canfar.models.active import ActiveConfig
from canfar.models.auth import AuthenticationCredential, X509Credential
from canfar.models.config_compat import (
    AuthContext,
    LegacyContextsMapping,
    credential_to_legacy_context,
    legacy_context_to_credential,
)
from canfar.models.http import Server
from canfar.models.registry import ContainerRegistry

log = get_logger(__name__)

_CADC_URI = AnyUrl("ivo://cadc.nrc.ca/skaha")

default_active = ActiveConfig(
    authentication="cadc",
    server=_CADC_URI,
)

default_authentication: list[AuthenticationCredential] = [
    X509Credential(
        idp="cadc",
        path=Path.home() / ".ssl" / "cadcproxy.pem",
        expiry=0.0,
    ),
]

default_servers: list[Server] = [
    Server(
        idp="cadc",
        name="canfar",
        uri=_CADC_URI,
        url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
        version="v1",
        auths=["x509"],
    ),
]


def _parse_dotted_path(path: str) -> list[str | int]:
    segments: list[str | int] = []
    for raw in path.split("."):
        if not raw:
            msg = f"Invalid path {path!r}: empty segment"
            raise ValueError(msg)
        segments.append(int(raw) if raw.isdigit() else raw)
    return segments


def _get_from_container(container: Any, key: str | int) -> Any:
    if isinstance(key, int):
        if not isinstance(container, list):
            msg = f"Expected list for index {key}"
            raise TypeError(msg)
        return container[key]

    if isinstance(container, BaseModel):
        return getattr(container, key)

    if isinstance(container, dict):
        return container[key]

    msg = f"Expected mapping or model for key {key!r}"
    raise TypeError(msg)


def _set_in_container(container: Any, key: str | int, value: Any) -> None:
    if isinstance(key, int):
        if not isinstance(container, list):
            msg = f"Expected list for index {key}"
            raise TypeError(msg)
        container[key] = value
        return

    if isinstance(container, dict):
        container[key] = value
        return

    msg = f"Expected mapping for key {key!r}"
    raise TypeError(msg)


def _ensure_child_container(parent: Any, key: str | int) -> Any:
    if isinstance(key, int):
        msg = "List indices are not supported for intermediate path segments"
        raise TypeError(msg)

    if not isinstance(parent, dict):
        msg = f"Expected mapping for key {key!r}"
        raise TypeError(msg)

    if key not in parent or parent[key] is None:
        parent[key] = {}
    return parent[key]


class ConsoleConfig(BaseModel):
    """Configuration for the CLI Console output.

    Args:
        BaseModel (pydantic.BaseModel): Base model for Pydantic configuration.
    """

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    width: int = Field(
        default=120,
        title="Console Width",
        description="Width of the console output.",
        ge=1,
    )
    file: Path | None = Field(
        default=None,
        title="Console File",
        description="File to write console output to. Defaults to stdout.",
    )


class Configuration(BaseSettings):
    """Unified configuration settings for CANFAR client and authentication.

    Config v1 separates authentication credentials from science platform
    servers. Active selection references an IDP key and server URI.
    """

    model_config = SettingsConfigDict(
        title="CANFAR Configuration",
        env_prefix="CANFAR_",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        json_schema_mode_override="serialization",
        str_strip_whitespace=True,
    )

    version: Literal[1] = Field(
        default=1,
        description="Configuration schema version.",
    )
    active: ActiveConfig = Field(
        default_factory=lambda: default_active.model_copy(deep=True),
        description="Active authentication and server selection.",
    )
    authentication: Annotated[
        list[AuthenticationCredential],
        Field(
            default_factory=lambda: [
                c.model_copy(deep=True) for c in default_authentication
            ],
            description="Saved authentication credentials keyed by IDP.",
        ),
    ]
    server: Annotated[
        list[Server],
        Field(
            default_factory=lambda: [s.model_copy(deep=True) for s in default_servers],
            description="Known science platform servers keyed by IDP.",
        ),
    ]
    registry: ContainerRegistry = Field(
        default_factory=ContainerRegistry,
        description="Container Registry Settings.",
    )
    console: ConsoleConfig = Field(
        default_factory=ConsoleConfig,
        description="Kwargs forwarded to rich.console.Console.",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to automatically load from YAML config file.

        Args:
            settings_cls: The settings class being configured.
            init_settings: Settings from init arguments.
            env_settings: Settings from env variables.
            dotenv_settings: Settings from .env files.
            file_secret_settings: Settings from secrets.

        Returns:
            A tuple of settings sources ordered by precedence.
        """
        return (
            init_settings,
            _CanfarEnvSettingsSource(settings_cls),
            _MigratedYamlConfigSettingsSource(settings_cls, yaml_file=CONFIG_PATH),
            file_secret_settings,
        )

    @model_validator(mode="after")
    def _validate_active_references(self) -> Configuration:
        """Validate active authentication and server exist in saved lists.

        Raises:
            ValueError: If active references are missing from saved records.

        Returns:
            The validated configuration.
        """
        auth_idps = {cred.idp for cred in self.authentication}
        if self.active.authentication not in auth_idps:
            msg = (
                f"Active authentication '{self.active.authentication}' "
                "not found in authentication list."
            )
            raise ValueError(msg)

        if self.active.server is not None:
            server_uris = {str(srv.uri) for srv in self.server if srv.uri is not None}
            if str(self.active.server) not in server_uris:
                msg = f"Active server '{self.active.server}' not found in server list."
                raise ValueError(msg)

        return self

    def save(self) -> None:
        """Save the current configuration to the default YAML file."""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = self.model_dump(mode="json", exclude_none=True)
            with CONFIG_PATH.open(mode="w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=True, indent=2)
        except (OSError, TypeError, ValidationError) as e:
            msg = f"Failed to save configuration to {CONFIG_PATH}: {e}"
            raise OSError(msg) from e

    def get_value(self, path: str) -> Any:
        """Get a nested configuration value via dotted path (e.g. 'console.width')."""
        value: Any = self
        for segment in _parse_dotted_path(path):
            value = _get_from_container(value, segment)
        return value

    def set_value(self, path: str, value: Any) -> Configuration:
        """Return a new validated Configuration with a dotted-path value updated."""
        segments = _parse_dotted_path(path)
        if not segments:
            msg = "Path cannot be empty"
            raise ValueError(msg)

        data = self.model_dump(mode="python")
        cursor: Any = data

        for segment in segments[:-1]:
            cursor = _ensure_child_container(cursor, segment)

        _set_in_container(cursor, segments[-1], value)
        return self.__class__.model_validate(data)

    def get_credential(self, idp: str) -> AuthenticationCredential:
        """Return the saved authentication credential for an IDP key.

        Args:
            idp: Canonical identity provider key.

        Returns:
            Matching authentication credential.

        Raises:
            KeyError: If no credential exists for ``idp``.
        """
        for credential in self.authentication:
            if credential.idp == idp:
                return credential
        msg = f"Authentication record for IDP '{idp}' not found."
        raise KeyError(msg)

    def get_server_by_uri(self, uri: str | AnyUrl) -> Server:
        """Return a known server by IVOA URI.

        Args:
            uri: Server URI to resolve.

        Returns:
            Matching server record.

        Raises:
            KeyError: If no server exists for ``uri``.
        """
        target = str(uri)
        for server in self.server:
            if server.uri is not None and str(server.uri) == target:
                return server
        msg = f"Server '{target}' not found."
        raise KeyError(msg)

    def get_active_server(self) -> Server:
        """Return the active science platform server record.

        Raises:
            KeyError: If no active server is selected.
        """
        if self.active.server is None:
            msg = "No active server selected."
            raise KeyError(msg)
        return self.get_server_by_uri(self.active.server)

    def get_server_for_idp(self, idp: str) -> Server:
        """Return the best-known server for an IDP.

        Uses the active server when it matches ``idp``; otherwise returns the
        first saved server for the IDP.

        Args:
            idp: Canonical identity provider key.

        Returns:
            Server record for the IDP.

        Raises:
            KeyError: If no server exists for ``idp``.
        """
        if self.active.authentication == idp and self.active.server is not None:
            return self.get_active_server()

        for server in self.server:
            if server.idp == idp:
                return server
        msg = f"No server found for IDP '{idp}'."
        raise KeyError(msg)

    @property
    def context(self) -> AuthContext:
        """Return the active authentication context in legacy shape.

        Returns:
            Legacy ``OIDC`` or ``X509`` model with embedded active server.
        """
        credential = self.get_credential(self.active.authentication)
        try:
            server = self.get_active_server()
        except KeyError:
            server = None
        return credential_to_legacy_context(credential, server)

    @property
    def contexts(self) -> LegacyContextsMapping:
        """Return a legacy dict-like view keyed by IDP."""
        return LegacyContextsMapping(self)

    def set_legacy_context(self, idp: str, context: AuthContext) -> None:
        """Update saved authentication (and optional server) from legacy context.

        Args:
            idp: Canonical identity provider key.
            context: Legacy authentication context to persist.
        """
        credential = legacy_context_to_credential(context, idp)
        updated: list[AuthenticationCredential] = []
        replaced = False
        for existing in self.authentication:
            if existing.idp == idp:
                updated.append(credential)
                replaced = True
            else:
                updated.append(existing)
        if not replaced:
            updated.append(credential)
        self.authentication = updated

        if context.server is not None:
            self._upsert_server(context.server.model_copy(update={"idp": idp}))

    def _upsert_server(self, server: Server) -> None:
        """Insert or replace a server record keyed by URI."""
        if server.uri is None:
            return
        target = str(server.uri)
        updated: list[Server] = []
        replaced = False
        for existing in self.server:
            if existing.uri is not None and str(existing.uri) == target:
                updated.append(server)
                replaced = True
            else:
                updated.append(existing)
        if not replaced:
            updated.append(server)
        self.server = updated


__all__ = ["AuthContext", "Configuration", "ConsoleConfig"]


class _CanfarEnvSettingsSource(EnvSettingsSource):
    """Environment source that ignores legacy ``CANFAR_ACTIVE`` string overrides."""

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        env_val, field_key, value_is_complex = super().get_field_value(
            field, field_name
        )
        if (
            field_name == "active"
            and isinstance(env_val, str)
            and not env_val.lstrip().startswith(("{", "["))
        ):
            return None, field_key, value_is_complex
        return env_val, field_key, value_is_complex


class _MigratedYamlConfigSettingsSource(YamlConfigSettingsSource):
    """YAML settings source that migrates legacy configuration before loading."""

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        *,
        yaml_file: Path,
        clock: Callable[[], float] | None = None,
    ) -> None:
        from canfar.config.migration import ensure_v1_config  # noqa: PLC0415

        ensure_v1_config(yaml_file, clock=clock)
        super().__init__(settings_cls, yaml_file=yaml_file)
