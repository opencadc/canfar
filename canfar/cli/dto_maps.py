"""Map domain models to command DTOs for machine output."""

from __future__ import annotations

from typing import TYPE_CHECKING

from canfar.models.dto.auth import (
    AuthenticationDto,
    AuthenticationListDto,
    AuthenticationShowDto,
)
from canfar.models.dto.context import ContextListDto, ContextPairDto, ContextShowDto
from canfar.models.dto.server import ServerListDto, ServerSummaryDto

if TYPE_CHECKING:
    from canfar.authentication import Authentication
    from canfar.models.http import Server


def authentication_dto(record: Authentication) -> AuthenticationDto:
    """Convert an authentication record to its machine DTO.

    Args:
        record: Domain authentication record.

    Returns:
        Command DTO for machine output.
    """
    return AuthenticationDto(
        idp=record.idp,
        name=record.name,
        mode=record.mode,
        expiry=record.expiry,
        active=record.active,
        server=record.server,
    )


def authentication_show_dto(record: Authentication) -> AuthenticationShowDto:
    """Build the ``auth show`` machine payload."""
    return AuthenticationShowDto(
        authentication=authentication_dto(record),
    )


def authentication_list_dto(
    records: list[Authentication],
) -> AuthenticationListDto:
    """Build the ``auth ls`` machine payload."""
    return AuthenticationListDto(
        authentications=[authentication_dto(item) for item in records],
    )


def server_summary_dto(
    server: Server, *, status: str | None = None
) -> ServerSummaryDto:
    """Convert a Server model to its machine DTO.

    Args:
        server: Persisted or discovered server record.
        status: Optional discovery reachability status.

    Returns:
        Command DTO for machine output.
    """
    return ServerSummaryDto(
        name=server.name,
        idp=server.idp,
        uri=str(server.uri) if server.uri is not None else None,
        url=str(server.url) if server.url is not None else None,
        status=status,
        version=server.version,
        auths=server.auths,
        cores=server.cores,
        ram=server.ram,
        gpus=server.gpus,
    )


def server_list_dto(servers: list[Server]) -> ServerListDto:
    """Build the ``server ls`` machine payload."""
    return ServerListDto(servers=[server_summary_dto(server) for server in servers])


def context_show_dto(
    authentication: Authentication | None,
    server: Server | None,
) -> ContextShowDto:
    """Build the ``context show`` machine payload."""
    return ContextShowDto(
        authentication=(
            authentication_dto(authentication) if authentication is not None else None
        ),
        server=server_summary_dto(server) if server is not None else None,
    )


def context_list_dto(
    pairs: list[tuple[Authentication, Server | None, bool]],
) -> ContextListDto:
    """Build the ``context ls`` machine payload."""
    return ContextListDto(
        pairs=[
            ContextPairDto(
                authentication=authentication_dto(auth),
                server=server_summary_dto(server) if server is not None else None,
                active=active,
            )
            for auth, server, active in pairs
        ],
    )
