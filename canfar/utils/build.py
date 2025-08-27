"""Utility functions for building parameters canfar client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from canfar.models.session import CreateRequest, FetchRequest
from canfar.utils import convert

if TYPE_CHECKING:
    from canfar.models.types import Kind, Status, View


def fetch_parameters(
    kind: Kind | None = None,
    status: Status | None = None,
    view: View | None = None,
) -> dict[str, Any]:
    """Build parameters for fetching sessions."""
    values: dict[str, Any] = {
        key: value
        for key, value in {"kind": kind, "status": status, "view": view}.items()
        if value
    }
    # Kind is an alias for type in the API.
    # It is renamed as kind to avoid conflicts with the built-in type function.
    # by_alias=true, returns, {"type": "headless"} instead of {"kind": "headless"}
    return FetchRequest(**values).model_dump(exclude_none=True, by_alias=True)


def create_parameters(
    name: str,
    image: str,
    cores: int | None = None,
    ram: int | None = None,
    kind: Kind = "headless",
    gpu: int | None = None,
    cmd: str | None = None,
    args: str | None = None,
    env: dict[str, Any] | None = None,
    replicas: int = 1,
) -> list[list[tuple[str, Any]]]:
    """Build parameters for creating sessions."""
    specification: CreateRequest = CreateRequest(
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
    payload: list[tuple[str, Any]] = []
    payloads: list[list[tuple[str, Any]]] = []
    if "env" not in data:
        data["env"] = {}
    for replica in range(replicas):
        if replicas == 1:
            data["name"] = name
        else:
            data["name"] = name + "-" + str(replica + 1)
        data["env"]["REPLICA_ID"] = str(replica + 1)
        data["env"]["REPLICA_COUNT"] = str(replicas)
        payload = convert.dict_to_tuples(data)
        payloads.append(payload)
    return payloads
