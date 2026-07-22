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
    from collections.abc import Iterable

    from pydantic.fields import FieldInfo

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)
from pydantic_settings.sources import EnvSettingsSource

from canfar import CONFIG_PATH, get_logger
from canfar.config.editor import get_value as _get_value
from canfar.config.editor import set_value as _set_value
from canfar.models.active import ActiveConfig
from canfar.models.auth import (
    AuthenticationCredential,
    X509Credential,
)
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
    banner: bool = Field(
        default=True,
        title="Console Banner",
        description="Show the active Server Selection in human CLI output.",
    )
    file: Path | None = Field(
        default=None,
        title="Console File",
        description="File to write console output to. Defaults to stdout.",
    )


class Configuration(BaseSettings):
    """Unified configuration settings for CANFAR client and authentication.

    Current configuration separates authentication credentials from science
    platform servers. Active selection references an IDP key and Server Name.
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
    def _normalize_and_validate_servers(self) -> Configuration:
        """Inject Server Names and validate Server and Storage Name keys."""
        updated: dict[str, Server] = {}
        server_name_by_storage_name: dict[str, str] = {}
        for name, server in self.servers.items():
            if not _SERVER_NAME_PATTERN.match(name):
                msg = (
                    f"Invalid server name '{name}': must match "
                    r"^[A-Za-z][A-Za-z0-9_-]*$"
                )
                raise ValueError(msg)
            for storage_name in server.storage:
                if previous_server_name := server_name_by_storage_name.get(
                    storage_name
                ):
                    msg = (
                        f"Duplicate Storage Name '{storage_name}' in Science Platform "
                        f"Servers '{previous_server_name}' and '{name}'."
                    )
                    raise ValueError(msg)
                server_name_by_storage_name[storage_name] = name
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

    def _validated_copy(self, **updates: Any) -> Configuration:
        """Validate a source-isolated copy of this complete Configuration."""
        data = {**self.model_dump(mode="python"), **updates}
        candidate = self.__class__.model_construct()
        self.__class__.__pydantic_validator__.validate_python(
            data,
            self_instance=candidate,
        )
        return candidate

    def _replace_state(
        self,
        *,
        active: ActiveConfig | None = None,
        authentication: dict[str, AuthenticationCredential] | None = None,
        servers: dict[str, Server] | None = None,
    ) -> None:
        """Validate and install a complete Authentication and Server state."""
        # Validate only this candidate; BaseSettings construction would reload and
        # merge persisted/environment sources, resurrecting keys being removed.
        candidate = self._validated_copy(
            active=self.active if active is None else active,
            authentication=(
                self.authentication if authentication is None else authentication
            ),
            servers=self.servers if servers is None else servers,
        )
        self.active = candidate.active
        self.authentication = candidate.authentication
        self.servers = candidate.servers

    def get_value(self, path: str) -> Any:
        """Get a nested configuration value via dotted path (e.g. 'console.width')."""
        return _get_value(self, path)

    def set_value(self, path: str, value: Any) -> Configuration:
        """Return a new validated Configuration with a dotted-path value updated."""
        return _set_value(self, path, value)

    def get_credential(self, idp: str) -> AuthenticationCredential:
        """Return the saved authentication credential for an IDP key.

        Args:
            idp: Canonical identity provider key.

        Returns:
            Matching authentication credential.

        Raises:
            KeyError: If no credential exists for ``idp``.
        """
        if idp not in self.authentication:
            msg = f"Authentication record for IDP '{idp}' not found."
            raise KeyError(msg)
        return self.authentication[idp]

    def _get_server_by_name(self, name: str) -> Server:
        """Return a known server by Server Name."""
        if name not in self.servers:
            msg = f"Server '{name}' not found."
            raise KeyError(msg)
        return self.servers[name]

    def upsert_credential(self, credential: AuthenticationCredential) -> None:
        """Insert or replace a validated Authentication Record.

        Args:
            credential: Authentication Record to store by its IDP key.
        """
        self._replace_state(
            authentication={**self.authentication, credential.idp: credential},
        )

    def update_credential(self, credential: AuthenticationCredential) -> None:
        """Replace an existing validated Authentication Record.

        Raises:
            KeyError: If no Authentication Record exists for the credential IDP.
        """
        self.get_credential(credential.idp)
        self.upsert_credential(credential)

    def set_active_authentication(self, idp: str) -> None:
        """Select an Authentication Record and its remembered Server, if any."""
        self.get_credential(idp)
        remembered = self.get_remembered_server_for_idp(idp)
        if remembered is not None:
            self.set_active_selection(idp, remembered)
            return

        selections = self._server_selection_history()
        server_name = self.active.server
        if server_name is not None:
            try:
                active_server = self.get_active_server()
            except KeyError:
                server_name = None
            else:
                if active_server.idp != idp:
                    server_name = None
        self._replace_state(
            active=self.active.model_copy(
                update={
                    "authentication": idp,
                    "server": server_name,
                    "servers": selections,
                },
            ),
        )

    def remove_authentication(self, idp: str) -> None:
        """Remove an Authentication Record and its Science Platform Servers."""
        authentication = dict(self.authentication)
        authentication.pop(idp, None)
        servers = {
            name: server for name, server in self.servers.items() if server.idp != idp
        }
        selections = {
            selected_idp: name
            for selected_idp, name in self.active.servers.items()
            if selected_idp != idp
        }

        if not authentication:
            self.purge_authentication()
            return

        active = self.active.model_copy(update={"servers": selections})
        if active.authentication == idp:
            active = active.model_copy(
                update={
                    "authentication": next(iter(authentication)),
                    "server": None,
                },
            )
        self._replace_state(
            active=active,
            authentication=authentication,
            servers=servers,
        )

    def purge_authentication(self) -> None:
        """Reset Authentication and Server state while preserving other settings."""
        self._replace_state(
            active=default_active.model_copy(deep=True),
            authentication={
                key: credential.model_copy(deep=True)
                for key, credential in default_authentication.items()
            },
            servers={
                name: server.model_copy(deep=True)
                for name, server in default_servers.items()
            },
        )

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
        for server in self.servers.values():
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
        return self._get_server_by_name(self.active.server)

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

        for server in self.servers.values():
            if server.idp == idp:
                return server
        msg = f"No server found for IDP '{idp}'."
        raise KeyError(msg)

    def get_remembered_server_for_idp(self, idp: str) -> Server | None:
        """Return the last selected server for ``idp`` when still valid.

        Args:
            idp: Canonical identity provider key.

        Returns:
            Matching server record, or ``None`` when no remembered selection is
            available for ``idp``.
        """
        name = self._server_selection_history().get(idp)
        if name is None or name not in self.servers:
            return None
        server = self.servers[name]
        if server.idp != idp:
            return None
        return server

    def _server_selection_history(self) -> dict[str, str]:
        """Return remembered selections seeded with the current active pair."""
        selections = dict(self.active.servers)
        active_name = self.active.server
        if active_name is None or active_name not in self.servers:
            return selections
        server = self.servers[active_name]
        if server.idp == self.active.authentication and server.name is not None:
            selections[self.active.authentication] = server.name
        return selections

    def set_active_selection(self, idp: str, server: Server) -> None:
        """Persist ``idp`` and ``server`` as the active pair.

        Args:
            idp: Canonical identity provider key.
            server: Server record to activate.

        Raises:
            ValueError: If the server has no Server Name.
        """
        if server.name is None:
            msg = "Server name is required for active selection."
            raise ValueError(msg)

        selected = server.model_copy(update={"idp": idp}, deep=True)
        servers = {**self.servers, server.name: selected}
        selections = self._server_selection_history()
        selections[idp] = server.name
        active = self.active.model_copy(
            update={
                "authentication": idp,
                "server": server.name,
                "servers": selections,
            },
        )
        self._replace_state(active=active, servers=servers)

    def upsert_server(self, server: Server) -> None:
        """Insert or replace a validated server record keyed by Server Name."""
        self.upsert_servers((server,))

    def upsert_servers(self, servers: Iterable[Server]) -> None:
        """Insert or replace validated server records in one state change."""
        updated = dict(self.servers)
        for server in servers:
            if server.name is not None:
                updated[server.name] = server
        self._replace_state(servers=updated)


__all__ = ["CONFIG_PATH", "Configuration", "ConsoleConfig"]


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
