"""Base helpers for command DTO serialization."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class DtoBase(BaseModel):
    """Base model for command-specific machine output DTOs.

    Declared fields are always emitted during serialization, including fields
    whose value is ``None``, so machine output keys remain stable.
    """

    model_config = ConfigDict(extra="forbid")


def dto_dump(model: BaseModel) -> dict[str, Any]:
    """Serialize a DTO for machine output with null fields included.

    Args:
        model: Pydantic model instance to serialize.

    Returns:
        JSON-compatible dictionary containing all declared fields.
    """
    return model.model_dump(mode="json", exclude_none=False)
