"""Tests for the prune CLI module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from canfar.cli.prune import PruneUsageMessage, prune

runner = CliRunner()


def _mock_async_session(mock_session_cls: MagicMock) -> AsyncMock:
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session
    return mock_session


def test_prune_success_and_usage_message() -> None:
    """Test prune command and custom usage message."""
    with patch("canfar.cli.prune.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.destroy_with.return_value = {"abc": True, "def": False}
        result = runner.invoke(prune, ["batch", "headless", "Succeeded"])

    assert result.exit_code == 0
    assert "Deleted 2 sessions" in result.stdout
    session.destroy_with.assert_awaited_once_with(
        prefix="batch", kind="headless", status="Succeeded"
    )

    usage = PruneUsageMessage(name="prune").get_usage(MagicMock())
    assert "canfar prune" in usage
