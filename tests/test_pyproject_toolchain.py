"""Invariant: mypy is gone, ty is configured in pyproject.toml."""

from __future__ import annotations

from pathlib import Path

import toml

_PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"


def _load() -> dict[str, object]:
    with _PYPROJECT.open() as f:
        return toml.load(f)


def test_mypy_config_absent() -> None:
    """The [tool.mypy] section must not exist after migrating to ty."""
    data = _load()
    assert "mypy" not in data.get("tool", {}), (
        "[tool.mypy] still present in pyproject.toml; migration to ty is incomplete."
    )


def test_ty_config_present() -> None:
    """A [tool.ty] section must exist after migrating from mypy."""
    data = _load()
    assert "ty" in data.get("tool", {}), (
        "[tool.ty] missing from pyproject.toml; ty is not configured."
    )


def test_mypy_dev_dependency_absent() -> None:
    """Mypy must not appear in [dependency-groups.dev] after the toolchain swap."""
    data = _load()
    dev_deps: list[str] = data.get("dependency-groups", {}).get("dev", [])
    assert not any(dep.startswith("mypy") for dep in dev_deps), (
        "mypy still listed as a dev dependency."
    )
