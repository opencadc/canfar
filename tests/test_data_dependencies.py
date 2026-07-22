"""Package metadata tests for the standard data dependencies."""

from __future__ import annotations

from pathlib import Path

import tomllib


def test_tagged_data_dependencies_are_standard_dependencies() -> None:
    """A standard CANFAR install includes both immutable upstream releases."""
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert (
        "vosfs @ git+https://github.com/shinybrar/vosfs@v0.6.0"
        in metadata["project"]["dependencies"]
    )
    assert (
        "fsspec-cli @ git+https://github.com/shinybrar/vosfs@fsspec-cli-v0.5.0"
        "#subdirectory=src/fsspec-cli" in metadata["project"]["dependencies"]
    )
    assert "data" not in metadata["project"].get("optional-dependencies", {})
