"""Container image payload models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Image(BaseModel):
    """Container image payload from the image API."""

    id: str = Field(..., description="Image identifier, including server.")
    types: list[str] = Field(default_factory=list, description="Image kinds.")
    digest: str = Field(..., description="Image digest (sha256).")
