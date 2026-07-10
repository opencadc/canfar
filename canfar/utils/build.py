"""Utility functions for building parameters canfar client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from canfar.models.session import CreateRequest, FetchRequest

if TYPE_CHECKING:
    from canfar.models.types import Kind, Status, View


def fetch_parameters(
    kind: Kind | None = None,
    status: Status | None = None,
    view: View | None = None,
) -> dict[str, Any]:
    """Build query parameters for fetching sessions.

    Args:
        kind: Session kind filter (serialized as ``type``).
        status: Session status filter.
        view: View scope filter.

    Returns:
        dict[str, Any]: Serialized fetch parameters with ``None`` fields omitted.
    """
    # Kind is an alias for type in the API.
    # It is renamed as kind to avoid conflicts with the built-in type function.
    # by_alias=true, returns, {"type": "headless"} instead of {"kind": "headless"}
    return FetchRequest(kind=kind, status=status, view=view).model_dump(  # ty: ignore[unknown-argument]
        exclude_none=True, by_alias=True
    )


def create_parameters(
    name: str | CreateRequest,
    image: str | None = None,
    cores: int | None = None,
    ram: int | None = None,
    kind: Kind = "headless",
    gpu: int | None = None,
    cmd: str | None = None,
    args: str | None = None,
    env: dict[str, Any] | None = None,
    replicas: int = 1,
) -> list[list[tuple[str, Any]]]:
    """Build form-encoded payloads for creating one or more sessions.

    Args:
        name: Domain request or base session name. Names are suffixed per replica.
        image: Container image reference when ``name`` is a string.
        cores: CPU core count.
        ram: RAM in gigabytes.
        kind: Session kind.
        gpu: GPU count (serialized as ``gpus``).
        cmd: Container command (headless sessions only).
        args: Container arguments (headless sessions only).
        env: Additional environment variables.
        replicas: Number of session replicas to create.

    Returns:
        list[list[tuple[str, Any]]]: One tuple payload per replica.
    """
    if isinstance(name, CreateRequest):
        specification = name
    else:
        if image is None:
            msg = "image is required when creating a Session from scalar arguments"
            raise TypeError(msg)
        specification = CreateRequest(
            name=name,
            image=image,
            cores=cores,
            ram=ram,
            kind=kind,
            gpus=gpu,
            cmd=cmd,
            args=args,
            env=env,
            replicas=replicas,
        )
    data: dict[str, Any] = specification.model_dump(exclude_none=True, by_alias=True)
    environment = data.pop("env", {})
    payloads: list[list[tuple[str, Any]]] = []
    replica_count = specification.replicas
    for replica in range(replica_count):
        data["name"] = (
            specification.name
            if replica_count == 1
            else f"{specification.name}-{replica + 1}"
        )
        replica_environment = environment | {
            "REPLICA_ID": str(replica + 1),
            "REPLICA_COUNT": str(replica_count),
        }
        payload = list(data.items())
        payload.extend(
            ("env", f"{key}={value}") for key, value in replica_environment.items()
        )
        payloads.append(payload)
    return payloads
