"""CANFAR client configuration models."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
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
from canfar.models.config_compat import AuthContext, LegacyContextsMapping
from canfar.models.http import Server
from canfar.models.registry import ContainerRegistry

log = get_logger(__name__)

_CADC_URI = AnyUrl("ivo://cadc.nrc.ca/skaha")
_CONFIG_KEY_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
_SERVER_NAME_PATTERN = _CONFIG_KEY_PATTERN

default_active = ActiveConfig(
    authentication="cadc",
    server="canfar",
)

default_authentication: dict[str, AuthenticationCredential] = {
    "cadc": X509Credential(
        idp="cadc",
        path=Path.home() / ".ssl" / "cadcproxy.pem",
        expiry=0.0,
    ),
}

default_servers: dict[str, Server] = {
    "canfar": Server(
        idp="cadc",
        uri=_CADC_URI,
        url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
        version="v1",
        auths=["x509"],
    ),
}


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

    Current configuration separates authentication credentials from science
    platform servers. Active selection references an IDP key and server URI.
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
        dict[str, AuthenticationCredential],
        Field(
            default_factory=lambda: {
                idp: c.model_copy(deep=True)
                for idp, c in default_authentication.items()
            },
            description="Saved authentication credentials keyed by IDP.",
        ),
    ]
    servers: Annotated[
        dict[str, Server],
        Field(
            default_factory=lambda: {
                name: s.model_copy(deep=True) for name, s in default_servers.items()
            },
            description="Known science platform servers keyed by Server Name.",
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
            _CheckedYamlConfigSettingsSource(settings_cls, yaml_file=CONFIG_PATH),
            file_secret_settings,
        )

    @model_validator(mode="after")
    def _inject_server_names(self) -> Configuration:
        """Inject dict keys into each server record and validate Server Names."""
        updated: dict[str, Server] = {}
        for name, server in self.servers.items():
            if not _SERVER_NAME_PATTERN.match(name):
                msg = (
                    f"Invalid server name '{name}': must match "
                    r"^[A-Za-z][A-Za-z0-9_-]*$"
                )
                raise ValueError(msg)
            updated[name] = server.model_copy(update={"name": name}, deep=True)
        self.servers = updated
        return self

    @model_validator(mode="before")
    @classmethod
    def _seed_credential_idps(cls, data: Any) -> Any:
        """Seed required credential ``idp`` fields from dict keys before parsing."""
        if isinstance(data, dict):
            authentication = data.get("authentication")
            if isinstance(authentication, dict):
                for idp, credential in authentication.items():
                    if isinstance(credential, dict):
                        credential.setdefault("idp", idp)
        return data

    @model_validator(mode="after")
    def _inject_credential_idps(self) -> Configuration:
        """Inject dict keys into each credential and validate IDP keys."""
        updated: dict[str, AuthenticationCredential] = {}
        for idp, credential in self.authentication.items():
            if not _CONFIG_KEY_PATTERN.match(idp):
                msg = (
                    f"Invalid IDP key '{idp}': must match "
                    r"^[A-Za-z][A-Za-z0-9_-]*$"
                )
                raise ValueError(msg)
            updated[idp] = credential.model_copy(update={"idp": idp}, deep=True)
        self.authentication = updated
        return self

    @model_validator(mode="after")
    def _validate_active_references(self) -> Configuration:
        """Validate active authentication and server exist in saved lists.

        Raises:
            ValueError: If active references are missing from saved records.

        Returns:
            The validated configuration.
        """
        auth_idps = set(self.authentication)
        if self.active.authentication not in auth_idps:
            msg = (
                f"Active authentication '{self.active.authentication}' "
                "not found in authentication list."
            )
            raise ValueError(msg)

        if self.active.server is not None and self.active.server not in self.servers:
            msg = f"Active server '{self.active.server}' not found in servers mapping."
            raise ValueError(msg)

        for idp, name in self.active.servers.items():
            if idp not in auth_idps:
                msg = (
                    f"Remembered server authentication '{idp}' "
                    "not found in authentication list."
                )
                raise ValueError(msg)
            try:
                server = self.servers[name]
            except KeyError as exc:
                msg = f"Remembered server '{name}' not found in servers mapping."
                raise ValueError(msg) from exc
            if server.idp != idp:
                msg = f"Remembered server '{name}' does not belong to IDP '{idp}'."
                raise ValueError(msg)

        return self

    def save(self) -> None:
        """Save the current configuration to the default YAML file."""
        from canfar.config.store import save_config  # noqa: PLC0415

        save_config(self)

    def get_value(self, path: str) -> Any:
        """Get a nested configuration value via dotted path (e.g. 'console.width')."""
        from canfar.config.editor import get_value  # noqa: PLC0415

        return get_value(self, path)

    def set_value(self, path: str, value: Any) -> Configuration:
        """Return a new validated Configuration with a dotted-path value updated."""
        from canfar.config.editor import set_value  # noqa: PLC0415

        return set_value(self, path, value)

    def get_credential(self, idp: str) -> AuthenticationCredential:
        """Return the saved authentication credential for an IDP key.

        Args:
            idp: Canonical identity provider key.

        Returns:
            Matching authentication credential.

        Raises:
            KeyError: If no credential exists for ``idp``.
        """
        from canfar.config.selection import get_credential  # noqa: PLC0415

        return get_credential(self, idp)

    def get_server_by_uri(self, uri: str | AnyUrl) -> Server:
        """Return a known server by IVOA URI.

        Args:
            uri: Server URI to resolve.

        Returns:
            Matching server record.

        Raises:
            KeyError: If no server exists for ``uri``.
        """
        from canfar.config.selection import get_server_by_uri  # noqa: PLC0415

        return get_server_by_uri(self, uri)

    def get_active_server(self) -> Server:
        """Return the active science platform server record.

        Raises:
            KeyError: If no active server is selected.
        """
        from canfar.config.selection import get_active_server  # noqa: PLC0415

        return get_active_server(self)

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
        from canfar.config.selection import get_server_for_idp  # noqa: PLC0415

        return get_server_for_idp(self, idp)

    def get_remembered_server_for_idp(self, idp: str) -> Server | None:
        """Return the last selected server for ``idp`` when still valid.

        Args:
            idp: Canonical identity provider key.

        Returns:
            Matching server record, or ``None`` when no remembered selection is
            available for ``idp``.
        """
        from canfar.config.selection import (  # noqa: PLC0415
            get_remembered_server_for_idp,
        )

        return get_remembered_server_for_idp(self, idp)

    def _server_selection_history(self) -> dict[str, str]:
        """Return remembered selections seeded with the current active pair."""
        from canfar.config.selection import server_selection_history  # noqa: PLC0415

        return server_selection_history(self)

    def set_active_selection(self, idp: str, server: Server) -> None:
        """Persist ``idp`` and ``server`` as the active pair.

        Args:
            idp: Canonical identity provider key.
            server: Server record to activate.

        Raises:
            ValueError: If the server has no Server Name.
        """
        from canfar.config.selection import set_active_selection  # noqa: PLC0415

        set_active_selection(self, idp, server)

    def with_active_selection(self, idp: str, server: Server) -> Configuration:
        """Return a copy using ``idp`` and ``server`` as the active pair.

        Args:
            idp: Canonical identity provider key.
            server: Server record to use for active server resolution.

        Returns:
            Configuration: Deep copy with the candidate Authentication and
            Server Selection installed.

        Raises:
            ValueError: If the server has no Server Name.
        """
        from canfar.config.selection import with_active_selection  # noqa: PLC0415

        return with_active_selection(self, idp, server)

    @property
    def context(self) -> AuthContext:
        """Return the active Authentication as a legacy ``AuthContext`` view.

        Returns:
            Legacy ``OIDC`` or ``X509`` model with embedded active server.
        """
        from canfar.config.selection import active_context  # noqa: PLC0415

        return active_context(self)

    @property
    def contexts(self) -> LegacyContextsMapping:
        """Return a legacy dict-like view keyed by IDP."""
        from canfar.config.selection import legacy_contexts  # noqa: PLC0415

        return legacy_contexts(self)

    def set_legacy_context(self, idp: str, context: AuthContext) -> None:
        """Update saved authentication (and optional server) from legacy context.

        Args:
            idp: Canonical identity provider key.
            context: Legacy ``AuthContext`` view to persist.
        """
        from canfar.config.selection import set_legacy_context  # noqa: PLC0415

        set_legacy_context(self, idp, context)

    def _upsert_server(self, server: Server) -> None:
        """Insert or replace a server record keyed by Server Name."""
        from canfar.config.selection import upsert_server  # noqa: PLC0415

        upsert_server(self, server)


__all__ = ["CONFIG_PATH", "AuthContext", "Configuration", "ConsoleConfig"]


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


class _CheckedYamlConfigSettingsSource(YamlConfigSettingsSource):
    """YAML settings source that rejects unsupported configuration before loading."""

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        *,
        yaml_file: Path,
    ) -> None:
        from canfar.config.migration import ensure_current_config  # noqa: PLC0415

        ensure_current_config(yaml_file)
        super().__init__(settings_cls, yaml_file=yaml_file)
