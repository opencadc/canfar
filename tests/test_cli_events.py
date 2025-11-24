"""Tests for the events CLI module."""

from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from canfar.cli.events import events

runner = CliRunner()


class TestEventsCLI:
    """Test cases for the events CLI functionality."""

    @patch("canfar.cli.events.AsyncSession")
    def test_events_command_success(self, mock_session_cls):
        """Test events command success."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        mock_events = [
            {
                "session-id": (
                    "Header\nType  Reason  Message  First-Seen  Last-Seen\n"
                    "Normal  Created  Created container  1m  1m"
                )
            }
        ]
        mock_session.events.return_value = mock_events

        result = runner.invoke(events, ["session-id"])

        assert result.exit_code == 0
        assert "Server events for session-id" in result.stdout
        assert "Normal" in result.stdout
        assert "Created" in result.stdout

    @patch("canfar.cli.events.AsyncSession")
    def test_events_command_no_events(self, mock_session_cls):
        """Test events command when no events found."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.events.return_value = []

        result = runner.invoke(events, ["session-id"])

        assert result.exit_code == 0
        assert "No events found" in result.stdout
