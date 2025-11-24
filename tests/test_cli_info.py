"""Tests for the info CLI module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from canfar.cli.info import _format, _utilization, info
from canfar.models.session import FetchResponse

runner = CliRunner()


class TestInfoCLI:
    """Test cases for the info CLI functionality."""

    def test_format(self):
        """Test _format function."""
        assert _format("any", None) == "[italic]Unknown[/italic]"
        assert _format("any", "") == "[italic]Unknown[/italic]"
        assert _format("any", []) == "[italic]Unknown[/italic]"
        assert _format("other", "value") == "value"

        now = datetime.now(timezone.utc)
        # humanize.naturaltime output varies, but usually contains "ago" or "now"
        assert isinstance(_format("startTime", now), str)

        future = now + timedelta(hours=2)
        # humanize.precisedelta output
        assert "2 hours" in _format("expiryTime", future)

    def test_utilization(self):
        """Test _utilization function."""
        # Mock FetchResponse object
        data = MagicMock(spec=FetchResponse)
        data.isFixedResources = True
        data.cpuCoresInUse = "1"
        data.requestedCPUCores = "2"

        # Test fixed resources
        result = _utilization(data, "cpuCoresInUse", "requestedCPUCores", "core(s)")
        assert "50%" in result

        # Test flexible resources
        data.isFixedResources = False
        data.cpuCoresInUse = "1"
        result = _utilization(data, "cpuCoresInUse", "requestedCPUCores", "core(s)")
        assert "1 core(s)" in result

        # Test unknown used
        data.cpuCoresInUse = None
        result = _utilization(data, "cpuCoresInUse", "requestedCPUCores", "core(s)")
        assert "[italic]Unknown[/italic]" in result

    @patch("canfar.cli.info.AsyncSession")
    def test_info_command_success(self, mock_session_cls):
        """Test info command success."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        mock_response = {
            "id": "test-id",
            "name": "test-name",
            "status": "Running",
            "type": "headless",
            "startTime": "2023-01-01T00:00:00Z",
            "expiryTime": "2023-01-02T00:00:00Z",
            "requestedCPUCores": "1",
            "requestedRAM": "1G",
            "requestedGPUCores": "0",
            "cpuCoresInUse": "0.1",
            "ramInUse": "0.1G",
            "gpuRAMInUse": "0",
            "isFixedResources": True,
        }
        mock_session.info.return_value = [mock_response]

        result = runner.invoke(info, ["test-id"])

        assert result.exit_code == 0
        assert "test-id" in result.stdout
        assert "test-name" in result.stdout

    @patch("canfar.cli.info.AsyncSession")
    def test_info_command_not_found(self, mock_session_cls):
        """Test info command when session not found."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.info.return_value = []

        result = runner.invoke(info, ["non-existent"])

        assert result.exit_code == 0
        assert "No information found" in result.stdout
