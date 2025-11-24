"""Tests for the create CLI module."""

from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from canfar.cli.create import create

runner = CliRunner()


class TestCreateCLI:
    """Test cases for the create CLI functionality."""

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_success(self, mock_session_cls):
        """Test create command success."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = ["session-id"]

        result = runner.invoke(
            create, ["headless", "image:tag", "--name", "test-session"]
        )

        assert result.exit_code == 0
        assert "Successfully created session" in result.stdout
        assert "session-id" in result.stdout

        mock_session.create.assert_called_once()
        call_args = mock_session.create.call_args[1]
        assert call_args["name"] == "test-session"
        assert call_args["kind"] == "headless"
        assert "image:tag" in call_args["image"]

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_multiple(self, mock_session_cls):
        """Test create command with multiple replicas."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = ["id-1", "id-2"]

        result = runner.invoke(create, ["headless", "image:tag", "--replicas", "2"])

        assert result.exit_code == 0
        assert "Successfully created 2 sessions" in result.stdout
        assert "id-1" in result.stdout
        assert "id-2" in result.stdout

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_failure(self, mock_session_cls):
        """Test create command failure."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = []

        result = runner.invoke(create, ["headless", "image:tag"])

        assert result.exit_code == 1
        assert "Failed to create session(s)" in result.stdout

    def test_create_command_dry_run(self):
        """Test create command dry run."""
        result = runner.invoke(create, ["headless", "image:tag", "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run complete" in result.stdout
        assert "Kind: headless" in result.stdout
        assert "Image: image:tag" in result.stdout

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_exception(self, mock_session_cls):
        """Test create command exception handling."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.side_effect = Exception("API Error")

        result = runner.invoke(create, ["headless", "image:tag"])

        assert result.exit_code == 1
        assert "Error: API Error" in result.stdout
