"""Tests for the open CLI module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from canfar.cli.open import open_command

runner = CliRunner()


def _mock_async_session(mock_session_cls: MagicMock) -> AsyncMock:
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session
    return mock_session


def test_open_command_opens_url_and_reports_missing_data() -> None:
    """Test open command opens sessions that include connect URLs."""
    with (
        patch("canfar.cli.open.AsyncSession") as session_cls,
        patch("canfar.cli.open.webbrowser.open_new_tab") as open_tab,
    ):
        session = _mock_async_session(session_cls)
        session.info.return_value = [
            {
                "id": "abc",
                "status": "Running",
                "connectURL": "https://example.test/session/abc",
            },
            {
                "id": "stopped",
                "status": "Stopped",
                "connectURL": "https://example.test/session/stopped",
            },
            {"id": "missing"},
        ]
        result = runner.invoke(open_command, ["abc", "stopped", "missing"])

    assert result.exit_code == 0
    assert "Opening session abc" in result.stdout
    assert "Opening session stopped" not in result.stdout
    assert "Session stopped is not ready to connect (status: Stopped)." in result.stderr
    assert "No connectURL found for session missing" in result.stderr
    open_tab.assert_called_once_with("https://example.test/session/abc")


def test_open_command_no_session_info() -> None:
    """Test open command reports missing session info."""
    with patch("canfar.cli.open.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.info.return_value = []
        result = runner.invoke(open_command, ["abc"])

    assert result.exit_code == 0
    assert "No information found" in result.stderr
