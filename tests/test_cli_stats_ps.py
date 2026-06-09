"""Integration tests for the stats and ps CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from canfar.cli.main import cli
from canfar.cli.ps import ps
from canfar.cli.stats import stats

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()

_SESSION_KEYS = frozenset(
    {
        "id",
        "userid",
        "runAsUID",
        "runAsGID",
        "supplementalGroups",
        "appid",
        "image",
        "type",
        "status",
        "name",
        "startTime",
        "expiryTime",
        "connectURL",
        "requestedRAM",
        "requestedCPUCores",
        "requestedGPUCores",
        "ramInUse",
        "gpuRAMInUse",
        "cpuCoresInUse",
        "gpuUtilization",
        "isFixedResources",
    }
)


def _session_payload(
    session_id: str,
    *,
    status: str = "Running",
    kind: str = "headless",
    **extra: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": session_id,
        "name": session_id,
        "type": kind,
        "status": status,
        "isFixedResources": True,
    }
    payload.update(extra)
    return payload


def _patch_config(path: Path):
    return patch("canfar.models.config.CONFIG_PATH", path)


def _mock_async_session(mock_session_cls: MagicMock) -> AsyncMock:
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session
    return mock_session


def test_stats_command_help() -> None:
    """Test stats command help executes successfully."""
    result = runner.invoke(cli, ["stats", "--help"])
    assert result.exit_code == 0


def test_ps_command_help() -> None:
    """Test ps command help executes successfully."""
    result = runner.invoke(cli, ["ps", "--help"])
    assert result.exit_code == 0


def test_ps_outputs_running_table_and_debug_anomalies() -> None:
    """Test ps table rendering with debug anomaly output."""
    payloads = [
        {
            "id": "running-1",
            "name": "run",
            "type": "headless",
            "status": "Running",
            "image": "images.canfar.net/skaha/terminal:latest",
            "startTime": "2025-01-01T00:00:00Z",
            "isFixedResources": True,
            "supplementalGroups": ["bad-group"],
        },
        {
            "id": "done-1",
            "name": "done",
            "type": "headless",
            "status": "Completed",
            "image": "images.canfar.net/skaha/terminal:latest",
            "startTime": "2025-01-02T00:00:00Z",
            "isFixedResources": True,
        },
    ]

    with patch("canfar.cli.ps.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.fetch.return_value = payloads
        result = runner.invoke(ps, ["--debug"])

    assert result.exit_code == 0
    assert "running-1" in result.stdout
    assert "done-1" not in result.stdout
    assert "Session Response Warnings" in result.stdout
    session.fetch.assert_awaited_once_with(kind=None, status=None)


def test_ps_quiet_prints_all_matching_session_ids() -> None:
    """Test ps quiet mode prints every matching session ID."""
    payloads = [
        {
            "id": "running-1",
            "name": "run",
            "type": "headless",
            "status": "Running",
            "isFixedResources": True,
        },
        {
            "id": "done-1",
            "name": "done",
            "type": "headless",
            "status": "Completed",
            "isFixedResources": True,
        },
        {
            "id": "running-2",
            "name": "run-2",
            "type": "headless",
            "status": "Running",
            "isFixedResources": True,
        },
    ]

    with patch("canfar.cli.ps.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.fetch.return_value = payloads
        result = runner.invoke(ps, ["--quiet"])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["running-1", "running-2"]

    with patch("canfar.cli.ps.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.fetch.return_value = payloads
        result = runner.invoke(ps, ["--quiet", "--all"])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["running-1", "done-1", "running-2"]


def test_ps_json_emits_filtered_session_array(tmp_path: Path) -> None:
    """``ps --json`` emits validated session models with running-only filtering."""
    config_path = tmp_path / "config.yaml"
    payloads = [
        _session_payload("running-1", status="Running"),
        _session_payload("done-1", status="Completed"),
    ]

    with (
        _patch_config(config_path),
        patch("canfar.cli.ps.AsyncSession") as session_cls,
    ):
        session = _mock_async_session(session_cls)
        session.fetch.return_value = payloads
        result = runner.invoke(ps, ["--json"])

    assert result.exit_code == 0
    assert not result.stdout.startswith("@")
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert [item["id"] for item in data] == ["running-1"]
    assert all(set(item) == _SESSION_KEYS for item in data)


def test_ps_yaml_emits_filtered_session_array(tmp_path: Path) -> None:
    """``ps --yaml`` emits the same filtered session payload as ``--json``."""
    config_path = tmp_path / "config.yaml"
    payloads = [_session_payload("running-1", status="Running")]

    with (
        _patch_config(config_path),
        patch("canfar.cli.ps.AsyncSession") as session_cls,
    ):
        session = _mock_async_session(session_cls)
        session.fetch.return_value = payloads
        result = runner.invoke(ps, ["--yaml"])

    assert result.exit_code == 0
    data = yaml.safe_load(result.stdout)
    assert isinstance(data, list)
    assert data[0]["id"] == "running-1"
    assert set(data[0]) == _SESSION_KEYS


def test_ps_json_kind_filter_parity(tmp_path: Path) -> None:
    """``ps --kind`` applies the same API filter in machine output mode."""
    config_path = tmp_path / "config.yaml"
    payloads = [
        _session_payload("headless-1", kind="headless"),
        _session_payload("notebook-1", kind="notebook"),
    ]

    with (
        _patch_config(config_path),
        patch("canfar.cli.ps.AsyncSession") as session_cls,
    ):
        session = _mock_async_session(session_cls)
        session.fetch.return_value = [payloads[0]]
        result = runner.invoke(ps, ["--kind", "headless", "--json"])

    assert result.exit_code == 0
    session.fetch.assert_awaited_once_with(kind="headless", status=None)
    data = json.loads(result.stdout)
    assert [item["id"] for item in data] == ["headless-1"]
    assert all(item["type"] == "headless" for item in data)


def test_ps_json_malformed_payload_keeps_stdout_pure(tmp_path: Path) -> None:
    """Malformed payloads warn on stderr; stdout stays a pure JSON array."""
    config_path = tmp_path / "config.yaml"
    payloads: list[object] = [
        _session_payload("running-1", status="Running"),
        "garbage-not-a-mapping",
    ]

    with (
        _patch_config(config_path),
        patch("canfar.cli.ps.AsyncSession") as session_cls,
    ):
        session = _mock_async_session(session_cls)
        session.fetch.return_value = payloads
        result = runner.invoke(ps, ["--json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert [item["id"] for item in data] == ["running-1"]
    assert "validation error" in result.stderr.lower()


def test_ps_quiet_with_json_exits_two() -> None:
    """``ps --quiet`` is incompatible with machine output flags."""
    result = runner.invoke(ps, ["--quiet", "--json"])
    assert result.exit_code == 2
    assert "quiet" in result.stderr.lower()


def test_ps_json_stdout_is_data_only(tmp_path: Path) -> None:
    """``ps --json`` suppresses the human-mode active-server banner."""
    config_path = tmp_path / "config.yaml"

    with (
        _patch_config(config_path),
        patch("canfar.cli.ps.AsyncSession") as session_cls,
    ):
        session = _mock_async_session(session_cls)
        session.fetch.return_value = []
        result = runner.invoke(ps, ["--json"])

    assert result.exit_code == 0
    assert not result.stdout.startswith("@")


def test_ps_allows_empty_running_view() -> None:
    """Test ps reports empty running view when only completed sessions exist."""
    with patch("canfar.cli.ps.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.fetch.return_value = [
            {
                "id": "done",
                "name": "done",
                "type": "headless",
                "status": "Completed",
                "isFixedResources": True,
            },
        ]
        result = runner.invoke(ps, [])

    assert result.exit_code == 0
    assert "No pending or running sessions found" in result.stdout


def test_stats_outputs_cluster_tables() -> None:
    """Test stats renders cluster table data."""
    with patch("canfar.cli.stats.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.stats.return_value = {
            "instances": {"desktopApp": 2, "notebook": 3, "total": 5},
            "cores": {"requestedCPUCores": 4, "cpuCoresAvailable": 64},
            "ram": {"requestedRAM": "8Gi", "ramAvailable": "128Gi"},
        }
        result = runner.invoke(stats, ["--debug"])

    assert result.exit_code == 0
    assert "CANFAR Platform Load" in result.stdout
    assert "Maximum Requests Size" in result.stdout
    session_cls.assert_called_once_with(loglevel="DEBUG")


@pytest.mark.slow
def test_stats_command_integration() -> None:
    """Test stats command integration (may fail without proper auth/config)."""
    result = runner.invoke(cli, ["stats"])
    # Command should exit cleanly even if it fails due to auth/config issues
    # We're just testing that it doesn't crash with exit code 2 (syntax error)
    assert result.exit_code in [0, 1]  # 0 = success, 1 = expected failure


@pytest.mark.slow
def test_ps_command_integration() -> None:
    """Test ps command integration (may fail without proper auth/config)."""
    result = runner.invoke(cli, ["ps"])
    # Command should exit cleanly even if it fails due to auth/config issues
    # We're just testing that it doesn't crash with exit code 2 (syntax error)
    assert result.exit_code in [0, 1]  # 0 = success, 1 = expected failure
