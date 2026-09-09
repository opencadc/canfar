"""Package metadata tests for the standard data dependencies."""

from __future__ import annotations

from importlib.metadata import distribution


def test_tagged_data_dependencies_are_standard_dependencies() -> None:
    """A standard CANFAR install includes both immutable upstream releases."""
    dist = distribution("canfar")
    requirements = dist.requires or []

    assert "vosfs @ git+https://github.com/shinybrar/vosfs@v0.8.0" in requirements
    assert (
        "fsspec-cli @ git+https://github.com/shinybrar/vosfs@fsspec-cli-v0.7.0"
        "#subdirectory=src/fsspec-cli" in requirements
    )
    assert "data" not in (dist.metadata.get_all("Provides-Extra") or [])
