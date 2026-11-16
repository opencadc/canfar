"""Utility functions for building parameters canfar client."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from canfar.models.session import CreateRequest, FetchRequest

if TYPE_CHECKING:
    from canfar.models.types import Kind, Status


def fetch_parameters(
    kind: Kind | None = None,
    status: Status | None = None,
) -> dict[str, Any]:
    """Build query parameters for fetching sessions.

    Args:
        kind: Session kind filter (serialized as ``type``).
        status: Session status filter.

    Returns:
        dict[str, Any]: Serialized fetch parameters with ``None`` fields omitted.
    """
    # Kind is an alias for type in the API.
    # It is renamed as kind to avoid conflicts with the built-in type function.
    # by_alias=true, returns, {"type": "headless"} instead of {"kind": "headless"}
    return FetchRequest(kind=kind, status=status).model_dump(  # ty: ignore[unknown-argument]
        exclude_none=True, by_alias=True
    )


def create_parameters(  # noqa: PLR0917
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
    *,
    maxfail: float | None = None,
) -> list[list[tuple[str, Any]]]:
    """Build form-encoded payloads for creating one or more sessions.

    A batch is one payload that carries ``replicas``; the Server sets the
    replica variables on each pod. Headless replicas are one payload per
    replica, each with a 1-based ``REPLICA_ID`` and ``REPLICA_COUNT``.

    Args:
        name: Domain request or base session name. Headless replica names are
            suffixed per replica.
        image: Container image reference when ``name`` is a string.
        cores: CPU core count.
        ram: RAM in gigabytes.
        kind: Session kind.
        gpu: GPU count (serialized as ``gpus``).
        cmd: Container command (headless and batch sessions only).
        args: Container arguments (headless and batch sessions only).
        env: Additional environment variables.
        replicas: Batch replica count, or the number of headless sessions.
        maxfail: Failed fraction of replicas that stops a batch.

    Returns:
        list[list[tuple[str, Any]]]: One tuple payload per create request.

    Warns:
        FutureWarning: When a headless request asks for more than one replica.
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
            maxfail=maxfail,
        )
    data: dict[str, Any] = specification.model_dump(exclude_none=True, by_alias=True)
    environment = data.pop("env", {})
    replica_count = specification.replicas
    if specification.kind == "batch":
        return [
            [
                *data.items(),
                ("replicas", replica_count),
                *(("env", f"{key}={value}") for key, value in environment.items()),
            ]
        ]
    if specification.fans_out:
        warnings.warn(
            "replicas above 1 for headless sessions are deprecated; use "
            "kind='batch' to run them as one session.",
            FutureWarning,
            # Point at the caller of Session.create, which calls this builder.
            stacklevel=3,
        )
    payloads: list[list[tuple[str, Any]]] = []
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
