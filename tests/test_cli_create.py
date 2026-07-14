"""Tests for the create CLI module."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import yaml
from typer.testing import CliRunner

from canfar.cli.create import create
from canfar.errors import ErrorCode, StructuredError
from canfar.models.session import CreateRequest

runner = CliRunner()


class TestCreateCLI:
    """Test cases for the create CLI functionality."""

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_success(self, mock_session_cls):
        """A fully populated command sends one domain request to the library."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = ["id-1", "id-2"]

        result = runner.invoke(
            create,
            [
                "headless",
                "skaha/worker:v1",
                "--name",
                "batch",
                "--cpu",
                "2",
                "--memory",
                "4",
                "--gpu",
                "1",
                "--env",
                "A=1",
                "--env",
                "B=two=parts",
                "--replicas",
                "2",
                "--",
                "python",
                "-m",
                "worker",
            ],
        )

        assert result.exit_code == 0
        mock_session.create.assert_awaited_once()
        assert mock_session.create.await_args.args == (
            CreateRequest(
                name="batch",
                image="images.canfar.net/skaha/worker:v1",
                cores=2,
                ram=4,
                kind="headless",
                gpus=1,
                cmd="python",
                args="-m worker",
                env={"A": "1", "B": "two=parts"},
                replicas=2,
            ),
        )
        assert mock_session.create.await_args.kwargs == {}

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_single_keeps_human_success_message(
        self,
        mock_session_cls,
    ):
        """One Session ID keeps the existing human success message."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = ["session-id"]

        result = runner.invoke(
            create,
            ["headless", "skaha/worker:v1", "--name", "single"],
        )

        assert result.exit_code == 0
        assert "Successfully created session 'single' (ID: session-id)" in result.stdout

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_multiple(self, mock_session_cls):
        """Test create command with multiple replicas."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = ["id-1", "id-2"]

        result = runner.invoke(
            create,
            ["headless", "skaha/worker:v1", "--replicas", "2"],
        )

        assert result.exit_code == 0
        assert "Successfully created 2 sessions" in result.stdout
        assert "id-1" in result.stdout
        assert "id-2" in result.stdout

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_json_success_is_a_raw_id_list(self, mock_session_cls):
        """JSON success emits one raw list even for one Session ID."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = ["session-id"]

        result = runner.invoke(create, ["headless", "skaha/worker:v1", "--json"])

        assert result.exit_code == 0
        assert json.loads(result.stdout) == ["session-id"]
        assert result.stderr == ""

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_debug_keeps_machine_stdout_data_only(
        self,
        mock_session_cls,
    ):
        """Parsed request diagnostics stay on stderr in machine mode."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = ["session-id"]

        result = runner.invoke(
            create,
            ["headless", "skaha/worker:v1", "--debug", "--json"],
        )

        assert result.exit_code == 0
        assert json.loads(result.stdout) == ["session-id"]
        assert "Debug: Parsed parameters" in result.stderr
        assert "Image: skaha/worker:v1" in result.stderr

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_yaml_partial_success_keeps_a_list(
        self,
        mock_session_cls,
    ):
        """A partial replica result remains a raw list in YAML output."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = ["id-1"]

        result = runner.invoke(
            create,
            ["headless", "skaha/worker:v1", "--replicas", "2", "--yaml"],
        )

        assert result.exit_code == 0
        assert yaml.safe_load(result.stdout) == ["id-1"]
        assert result.stderr == ""

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_failure(self, mock_session_cls):
        """Test create command failure."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = []

        result = runner.invoke(create, ["headless", "skaha/worker:v1"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert "Failed to create session(s)" in result.stderr
        assert "CANFAR_TIMEOUT" in result.stderr
        assert "canfar --log-level debug create" in result.stderr

    @pytest.mark.parametrize(
        ("flag", "load"),
        [("--json", json.loads), ("--yaml", yaml.safe_load)],
    )
    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_machine_empty_is_transport_failure(
        self,
        mock_session_cls,
        flag,
        load,
    ):
        """An empty library result is one structured machine error."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = []

        result = runner.invoke(create, ["headless", "skaha/worker:v1", flag])

        assert result.exit_code == 1
        assert result.stdout == ""
        error = StructuredError.model_validate(load(result.stderr))
        assert error.code == ErrorCode.TRANSPORT_FAILURE.value

    @pytest.mark.parametrize(
        ("flag", "load"),
        [("--json", json.loads), ("--yaml", yaml.safe_load)],
    )
    @pytest.mark.parametrize(
        "invalid_args",
        [("--cpu", "-1"), ("--env", "BROKEN")],
    )
    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_machine_validation_failure_is_structured(
        self,
        mock_session_cls,
        invalid_args,
        flag,
        load,
    ):
        """Invalid command input fails before the Session boundary opens."""
        result = runner.invoke(
            create,
            ["headless", "skaha/worker:v1", *invalid_args, flag],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        error = StructuredError.model_validate(load(result.stderr))
        assert error.code == ErrorCode.COMMAND_VALIDATION_FAILED.value
        mock_session_cls.assert_not_called()

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_validation_failure_keeps_human_diagnostics(
        self,
        mock_session_cls,
    ):
        """Human validation failure keeps detailed diagnostics and exit one."""
        result = runner.invoke(
            create,
            ["headless", "skaha/worker:v1", "--cpu", "-1"],
        )

        assert result.exit_code == 1
        assert "Error:" in result.stderr
        assert "validation error for CreateRequest" in result.stderr
        assert "Traceback" in result.stderr
        mock_session_cls.assert_not_called()

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_malformed_environment_keeps_human_message(
        self,
        mock_session_cls,
    ):
        """Human malformed-environment input keeps its existing message."""
        result = runner.invoke(
            create,
            ["headless", "skaha/worker:v1", "--env", "BROKEN"],
        )

        assert result.exit_code == 1
        assert "Error: Invalid env variable: BROKEN" in result.stderr
        assert "Traceback" not in result.stderr
        mock_session_cls.assert_not_called()

    def test_create_command_dry_run(self):
        """Test create command dry run."""
        result = runner.invoke(
            create,
            ["headless", "skaha/worker:v1", "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry run complete" in result.stdout
        assert "Kind: headless" in result.stdout
        assert "Image: skaha/worker:v1" in result.stdout

    def test_create_command_rejects_dry_run_with_machine_output(self):
        """Dry-run diagnostics cannot contaminate machine stdout."""
        result = runner.invoke(
            create,
            ["headless", "skaha/worker:v1", "--dry-run", "--json"],
        )

        assert result.exit_code == 2
        assert result.stdout == ""
        assert "--dry-run" in result.stderr

    def test_create_command_rejects_conflicting_machine_formats(self):
        """The shared resolver rejects simultaneous JSON and YAML output."""
        result = runner.invoke(
            create,
            ["headless", "skaha/worker:v1", "--json", "--yaml"],
        )

        assert result.exit_code == 2
        assert result.stdout == ""
        assert "Conflicting machine output flags" in result.stderr

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_exception(self, mock_session_cls):
        """Test create command exception handling."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.side_effect = httpx.HTTPError("API Error")

        result = runner.invoke(create, ["headless", "skaha/worker:v1"])

        assert result.exit_code == 1
        assert "Error: API Error" in result.stderr

    @pytest.mark.parametrize(
        ("flag", "load"),
        [("--json", json.loads), ("--yaml", yaml.safe_load)],
    )
    @pytest.mark.parametrize("phase", ["enter", "body", "exit"])
    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_machine_exception_is_secret_safe_transport_failure(
        self,
        mock_session_cls,
        phase,
        flag,
        load,
    ):
        """Session lifecycle errors never expose raw details in machine mode."""
        secret = "upstream-create-secret-sentinel"
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = ["session-id"]
        failing_call = {
            "enter": mock_session_cls.return_value.__aenter__,
            "body": mock_session.create,
            "exit": mock_session_cls.return_value.__aexit__,
        }[phase]
        failing_call.side_effect = httpx.HTTPError(secret)

        result = runner.invoke(create, ["headless", "skaha/worker:v1", flag])

        assert result.exit_code == 1
        assert result.stdout == ""
        error = StructuredError.model_validate(load(result.stderr))
        assert error.code == ErrorCode.TRANSPORT_FAILURE.value
        assert secret not in result.stderr
        assert "Traceback" not in result.stderr

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_keyboard_interrupt_keeps_human_exit(
        self,
        mock_session_cls,
    ):
        """User cancellation keeps its human message and exit code."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.side_effect = KeyboardInterrupt

        result = runner.invoke(create, ["headless", "skaha/worker:v1"])

        assert result.exit_code == 130
        assert result.stdout == ""
        assert "Operation cancelled by user" in result.stderr

    @pytest.mark.parametrize(
        ("flag", "load"),
        [("--json", json.loads), ("--yaml", yaml.safe_load)],
    )
    @pytest.mark.parametrize("phase", ["enter", "body", "exit"])
    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_machine_keyboard_interrupt_is_structured(
        self,
        mock_session_cls,
        phase,
        flag,
        load,
    ):
        """Lifecycle cancellation keeps exit 130 with one stable error code."""
        secret = "cancelled-create-secret-sentinel"
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = ["session-id"]
        failing_call = {
            "enter": mock_session_cls.return_value.__aenter__,
            "body": mock_session.create,
            "exit": mock_session_cls.return_value.__aexit__,
        }[phase]
        failing_call.side_effect = KeyboardInterrupt(secret)

        result = runner.invoke(create, ["headless", "skaha/worker:v1", flag])

        assert result.exit_code == 130
        assert result.stdout == ""
        error = StructuredError.model_validate(load(result.stderr))
        assert error.code == ErrorCode.COMMAND_CANCELLED.value
        assert secret not in result.stderr
        assert "Traceback" not in result.stderr
