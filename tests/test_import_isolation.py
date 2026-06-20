"""Tests that the suite stays isolated from the developer's CANFAR config."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path


def test_conftest_isolates_home() -> None:
    """Pytest must not read the developer ``~/.canfar/config.yaml`` at collection."""
    assert Path(os.environ["HOME"]) == Path(os.environ["CANFAR_TEST_HOME"])


def test_stale_list_config_breaks_canfar_import_without_home_isolation(
    tmp_path: Path,
) -> None:
    """Legacy list-shaped config under ``HOME`` prevents importing canfar."""
    home = tmp_path / "stale-home"
    config_dir = home / ".canfar"
    config_dir.mkdir(parents=True)
    config_dir.joinpath("config.yaml").write_text(
        """
version: 1
active:
  authentication: cadc
  server: ivo://cadc.nrc.ca/skaha
authentication:
  - idp: cadc
    mode: x509
    path: /tmp/cert.pem
    expiry: 0
server:
  - idp: cadc
    name: canfar
    uri: ivo://cadc.nrc.ca/skaha
    url: https://ws-uv.canfar.net/skaha
    version: v1
    auths: [x509]
""".strip(),
        encoding="utf-8",
    )

    script = """
import os
import sys
from pathlib import Path

os.environ["HOME"] = sys.argv[1]
import canfar  # noqa: F401
"""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(home)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "ValidationError" in result.stderr


def _function_local_imports(source: str) -> list[tuple[str, str]]:
    """Return (function_name, module) pairs for every function-local import."""
    tree = ast.parse(source)
    results: list[tuple[str, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for child in ast.walk(node):
            if child is node:
                continue
            if isinstance(child, ast.Import):
                results.extend((node.name, alias.name) for alias in child.names)
            elif isinstance(child, ast.ImportFrom):
                module = child.module or ""
                results.append((node.name, module))
    return results


def test_no_function_local_selection_imports_in_models_config() -> None:
    """No function-local imports from ``config.selection`` in ``models/config.py``.

    The import cycle between ``canfar.models.config`` and
    ``canfar.config.selection`` must be broken: all ``selection`` imports
    belong at module level in ``models/config.py``.
    """
    config_source = Path("canfar/models/config.py").read_text(encoding="utf-8")
    local_imports = _function_local_imports(config_source)

    offenders = [
        (fn, mod) for fn, mod in local_imports if "canfar.config.selection" in mod
    ]
    assert offenders == [], (
        f"Function-local selection imports found in models/config.py: {offenders}"
    )


def test_no_function_local_editor_imports_in_models_config() -> None:
    """No function-local imports from ``config.editor`` in ``models/config.py``."""
    config_source = Path("canfar/models/config.py").read_text(encoding="utf-8")
    local_imports = _function_local_imports(config_source)

    offenders = [
        (fn, mod) for fn, mod in local_imports if "canfar.config.editor" in mod
    ]
    assert offenders == [], (
        f"Function-local editor imports found in models/config.py: {offenders}"
    )


def test_selection_importable_before_config() -> None:
    """``canfar.config.selection`` can be imported before ``canfar.models.config``."""
    script = """
import sys
# Clear any cached canfar modules
for k in list(sys.modules.keys()):
    if "canfar" in k:
        del sys.modules[k]

import canfar.config.selection  # noqa: F401
import canfar.models.config  # noqa: F401
"""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
