"""Package metadata tests for the standard data dependencies."""

from __future__ import annotations

from pathlib import Path

_PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"


def test_tagged_data_dependencies_are_standard_dependencies() -> None:
    """A standard CANFAR install includes both immutable upstream releases."""
    pyproject = _PYPROJECT.read_text(encoding="utf-8")

    assert "vosfs @ git+https://github.com/shinybrar/vosfs@v0.8.0" in pyproject
    assert (
        "fsspec-cli @ git+https://github.com/shinybrar/vosfs@fsspec-cli-v0.7.0"
        "#subdirectory=src/fsspec-cli" in pyproject
    )
    assert "[project.optional-dependencies]" not in pyproject
