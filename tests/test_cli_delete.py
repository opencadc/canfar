"""Tests for the delete CLI module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from canfar.cli.delete import delete

runner = CliRunner()


def _mock_async_session(mock_session_cls: MagicMock) -> AsyncMock:
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session
    return mock_session


def test_delete_force_success_error_and_cancel() -> None:
    """Test forced delete, handled delete error, and prompt cancellation."""
    with patch("canfar.cli.delete.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.destroy.return_value = {"abc": True}
        result = runner.invoke(delete, ["--force", "abc"])

    assert result.exit_code == 0
    assert "Successfully deleted" in result.stdout

    with patch("canfar.cli.delete.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.destroy.side_effect = RuntimeError("delete failed")
        result = runner.invoke(delete, ["--force", "abc"])

    assert result.exit_code == 0
    assert "Error during deletion: delete failed" in result.stdout

    with patch("canfar.cli.delete.Confirm.ask", return_value=False):
        result = runner.invoke(delete, ["abc"])

    assert result.exit_code == 0
