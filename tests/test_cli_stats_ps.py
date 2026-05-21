"""Integration tests for the stats and ps CLI commands."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from canfar.cli.main import cli
from canfar.cli.ps import ps
from canfar.cli.stats import stats

runner = CliRunner()


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


def test_ps_quiet_prints_first_session_id() -> None:
    """Test ps quiet mode prints the first session ID."""
    with patch("canfar.cli.ps.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.fetch.return_value = [
            {
                "id": "first-id",
                "name": "run",
                "type": "headless",
                "status": "Running",
                "isFixedResources": True,
            }
        ]
        result = runner.invoke(ps, ["--quiet"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "first-id"


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
