"""Tests that the suite stays isolated from the developer's CANFAR config."""

from __future__ import annotations

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
