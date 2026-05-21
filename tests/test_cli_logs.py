"""Tests for the logs CLI module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from canfar.cli.logs import logs

runner = CliRunner()


def _mock_async_session(mock_session_cls: MagicMock) -> AsyncMock:
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session
    return mock_session


def test_logs_outputs_logs_and_empty_message() -> None:
    """Test logs command output and empty result message."""
    with patch("canfar.cli.logs.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.logs.return_value = {"abc": "hello\nworld"}
        result = runner.invoke(logs, ["abc"])

    assert result.exit_code == 0
    assert "Logs for session abc" in result.stdout
    assert "hello" in result.stdout

    with patch("canfar.cli.logs.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.logs.return_value = {}
        result = runner.invoke(logs, ["abc"])

    assert result.exit_code == 0
    assert "No logs found" in result.stdout


def test_logs_reports_fetch_error() -> None:
    """Test logs command reports fetch errors."""
    with patch("canfar.cli.logs.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.logs.side_effect = RuntimeError("boom")
        result = runner.invoke(logs, ["abc"])

    assert result.exit_code == 1
    assert "Could not fetch logs" in result.stdout
    assert "boom" in result.stdout
