"""Tests for the create CLI module."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx2
import pytest
import yaml
from rich.text import Text
from typer.testing import CliRunner

from canfar.cli.main import cli
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
            cli,
            [
                "create",
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
            cli,
            ["create", "headless", "skaha/worker:v1", "--name", "single"],
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
            cli,
            ["create", "headless", "skaha/worker:v1", "--replicas", "2"],
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

        result = runner.invoke(
            cli,
            ["create", "headless", "skaha/worker:v1", "--output", "json"],
        )

        assert result.exit_code == 0
        assert json.loads(result.stdout) == ["session-id"]
        assert result.stderr == ""

    @patch("canfar.cli.create.AsyncSession")
    def test_create_output_option_stops_at_command_delimiter(
        self,
        mock_session_cls,
    ):
        """Only the output option before ``--`` is parsed by ``create``."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.return_value = ["session-id"]

        result = runner.invoke(
            cli,
            [
                "create",
                "headless",
                "skaha/worker:v1",
                "--output",
                "json",
                "--",
                "echo",
                "-o",
                "yaml",
                "--output",
                "json",
            ],
        )

        assert result.exit_code == 0
        assert json.loads(result.stdout) == ["session-id"]
        request = mock_session.create.await_args.args[0]
        assert request.cmd == "echo"
        assert request.args == "-o yaml --output json"

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
            cli,
            ["create", "headless", "skaha/worker:v1", "--debug", "--output", "json"],
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
            cli,
            [
                "create",
                "headless",
                "skaha/worker:v1",
                "--replicas",
                "2",
                "--output",
                "yaml",
            ],
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

        result = runner.invoke(cli, ["create", "headless", "skaha/worker:v1"])

        assert result.exit_code == 1
        assert result.stdout.startswith("@")
        assert "Failed to create session(s)" in result.stderr
        assert "CANFAR_TIMEOUT" in result.stderr
        assert "canfar --log-level debug create" in result.stderr

    @pytest.mark.parametrize(
        ("flag", "load"),
        [
            (["--output", "json"], json.loads),
            (["--output", "yaml"], yaml.safe_load),
        ],
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

        result = runner.invoke(cli, ["create", "headless", "skaha/worker:v1", *flag])

        assert result.exit_code == 1
        assert result.stdout == ""
        error = StructuredError.model_validate(load(result.stderr))
        assert error.code == ErrorCode.TRANSPORT_FAILURE.value

    @pytest.mark.parametrize(
        ("flag", "load"),
        [
            (["--output", "json"], json.loads),
            (["--output", "yaml"], yaml.safe_load),
        ],
    )
    @pytest.mark.parametrize("invalid_args", [("--env", "BROKEN")])
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
            cli,
            ["create", "headless", "skaha/worker:v1", *invalid_args, *flag],
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
        result = runner.invoke(cli, ["create", "headless", "worker"])

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
            cli,
            ["create", "headless", "skaha/worker:v1", "--env", "BROKEN"],
        )

        assert result.exit_code == 1
        assert "Error: Invalid env variable: BROKEN" in result.stderr
        assert "Traceback" not in result.stderr
        mock_session_cls.assert_not_called()

    def test_create_command_dry_run(self):
        """Test create command dry run."""
        result = runner.invoke(
            cli,
            ["create", "headless", "skaha/worker:v1", "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry run complete" in result.stdout
        assert "Kind: headless" in result.stdout
        assert "Image: skaha/worker:v1" in result.stdout

    def test_create_command_rejects_dry_run_with_machine_output(self):
        """Dry-run diagnostics cannot contaminate machine stdout."""
        result = runner.invoke(
            cli,
            [
                "create",
                "headless",
                "skaha/worker:v1",
                "--dry-run",
                "--output",
                "json",
            ],
        )

        assert result.exit_code == 2
        assert result.stdout == ""
        assert "--dry-run" in result.stderr

    @patch("canfar.cli.create.AsyncSession")
    def test_create_command_exception(self, mock_session_cls):
        """Test create command exception handling."""
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session.create.side_effect = httpx2.HTTPError("API Error")

        result = runner.invoke(cli, ["create", "headless", "skaha/worker:v1"])

        assert result.exit_code == 1
        assert "Error: API Error" in result.stderr

    @pytest.mark.parametrize(
        ("flag", "load"),
        [
            (["--output", "json"], json.loads),
            (["--output", "yaml"], yaml.safe_load),
        ],
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
        failing_call.side_effect = httpx2.HTTPError(secret)

        result = runner.invoke(cli, ["create", "headless", "skaha/worker:v1", *flag])

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

        result = runner.invoke(cli, ["create", "headless", "skaha/worker:v1"])

        assert result.exit_code == 130
        assert result.stdout.startswith("@")
        assert "Operation cancelled by user" in result.stderr

    @pytest.mark.parametrize(
        ("flag", "load"),
        [
            (["--output", "json"], json.loads),
            (["--output", "yaml"], yaml.safe_load),
        ],
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

        result = runner.invoke(cli, ["create", "headless", "skaha/worker:v1", *flag])

        assert result.exit_code == 130
        assert result.stdout == ""
        error = StructuredError.model_validate(load(result.stderr))
        assert error.code == ErrorCode.COMMAND_CANCELLED.value
        assert secret not in result.stderr
        assert "Traceback" not in result.stderr


def _save_limited_server(path: Path) -> None:
    """Save an active Server that advertises Session resource limits."""
    path.write_text(
        yaml.dump(
            {
                "version": 1,
                "active": {"authentication": "cadc", "server": "canSRC"},
                "authentication": {"cadc": {"mode": "x509"}},
                "servers": {
                    "canSRC": {
                        "idp": "cadc",
                        "uri": "ivo://canfar.net/src/skaha",
                        "url": "https://src.canfar.net/skaha",
                        "version": "v1",
                        "resources": {
                            "flexible": {
                                "cores": {"min": 1, "max": 2},
                                "ram": {"min": 2, "max": 4},
                            },
                            "fixed": {
                                "cores": {"min": 1, "max": 34},
                                "ram": {"min": 1, "max": 384},
                            },
                            "gpus": {"min": 0, "max": 0},
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )


class TestCreateServerLimits:
    """Typer validates resource options against the active Server's limits."""

    @pytest.mark.parametrize(
        ("arguments", "message"),
        [
            (
                ["--cpu", "64"],
                "Invalid value for '--cpu' / '-c': 64 is not in the range 1<=x<=34.",
            ),
            (
                ["--memory", "512"],
                (
                    "Invalid value for '--memory' / '-m': 512 is not in the range "
                    "1<=x<=384."
                ),
            ),
            (
                ["--gpu", "1"],
                "Invalid value for '--gpu' / '-g': 1 is not in the range 0<=x<=0.",
            ),
        ],
    )
    @pytest.mark.parametrize("flag", [[], ["-o", "json"]], ids=["human", "json"])
    @patch("canfar.cli.create.AsyncSession")
    def test_rejects_values_outside_active_server_limits(
        self,
        mock_session_cls,
        tmp_path: Path,
        arguments: list[str],
        message: str,
        flag: list[str],
    ) -> None:
        """Out-of-range values are usage errors on stderr, before any request."""
        config_path = tmp_path / "config.yaml"
        _save_limited_server(config_path)

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            result = runner.invoke(
                cli,
                ["create", "headless", "skaha/worker:v1", *arguments, *flag],
                env={"COLUMNS": "200"},
            )

        assert result.exit_code == 2
        assert result.stdout == ""
        assert message in " ".join(Text.from_ansi(result.stderr).plain.split())
        mock_session_cls.assert_not_called()

    def test_accepts_requests_within_the_server_limits(self, tmp_path: Path) -> None:
        """The largest values the Server accepts still pass."""
        config_path = tmp_path / "config.yaml"
        _save_limited_server(config_path)

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            result = runner.invoke(
                cli,
                [
                    *("create", "headless", "skaha/worker:v1"),
                    *("--cpu", "34", "--memory", "384", "--dry-run"),
                ],
            )

        assert result.exit_code == 0, result.stderr
        assert "Dry run complete." in result.stdout

    @pytest.mark.parametrize(
        ("arguments", "message"),
        [
            (["--cpu", "257"], "257 is not in the range 1<=x<=256."),
            (["--memory", "0"], "0 is not in the range 1<=x<=512."),
            (["--gpu", "29"], "29 is not in the range 1<=x<=28."),
            (["--replicas", "257"], "257 is not in the range 1<=x<=256."),
        ],
    )
    def test_unknown_server_limits_keep_the_client_bounds(
        self, arguments: list[str], message: str
    ) -> None:
        """Without saved limits, the client's own bounds still apply."""
        result = runner.invoke(
            cli,
            ["create", "headless", "skaha/worker:v1", *arguments],
            env={"COLUMNS": "200"},
        )

        assert result.exit_code == 2
        assert message in " ".join(Text.from_ansi(result.stderr).plain.split())


@pytest.mark.parametrize(
    ("limited", "expected"),
    [
        (
            True,
            [
                "<int range> [1<=x<=34] Number of CPU cores. [default: flexible ≤ 2]",
                "<int range> [1<=x<=384] Amount of RAM in GB. [default: flexible ≤ 4]",
                "<int range> [0<=x<=0] Number of GPUs.",
            ],
        ),
        (
            False,
            [
                (
                    "<int range> [1<=x<=256] Number of CPU cores. "
                    "[default: flexible, set by the Server]"
                ),
                (
                    "<int range> [1<=x<=512] Amount of RAM in GB. "
                    "[default: flexible, set by the Server]"
                ),
                "<int range> [1<=x<=28] Number of GPUs.",
            ],
        ),
    ],
    ids=["active-server-limits", "unknown-limits"],
)
def test_create_help_shows_the_active_server_ranges(
    tmp_path: Path, limited: bool, expected: list[str]
) -> None:
    """Typer shows each resource range, and the flexible limit as the default."""
    config_path = tmp_path / "config.yaml"
    if limited:
        _save_limited_server(config_path)

    with patch("canfar.models.config.CONFIG_PATH", config_path):
        result = runner.invoke(cli, ["create", "--help"], env={"COLUMNS": "200"})

    assert result.exit_code == 0
    help_text = " ".join(result.stdout.split())
    for text in expected:
        assert text in help_text
    assert "canSRC" not in help_text


@pytest.mark.parametrize(
    ("resources", "arguments", "message"),
    [
        (
            {"fixed": {"cores": {"min": 1, "max": 300}}},
            ["--cpu", "300"],
            "300 is not in the range 1<=x<=256.",
        ),
        (
            {"gpus": {"min": 0, "max": 0}},
            ["--gpu", "1"],
            "1 is not in the range 0<=x<=0.",
        ),
    ],
    ids=["server-above-client-bound", "server-without-gpus"],
)
def test_server_ranges_never_widen_the_client_bounds(
    tmp_path: Path,
    resources: dict[str, object],
    arguments: list[str],
    message: str,
) -> None:
    """Typer accepts only values that both the client and the Server allow."""
    config_path = tmp_path / "config.yaml"
    _save_limited_server(config_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["servers"]["canSRC"]["resources"] = resources
    config_path.write_text(yaml.dump(config), encoding="utf-8")

    with patch("canfar.models.config.CONFIG_PATH", config_path):
        result = runner.invoke(
            cli,
            ["create", "headless", "skaha/worker:v1", *arguments, "--dry-run"],
            env={"COLUMNS": "200"},
        )

    assert result.exit_code == 2
    assert message in " ".join(Text.from_ansi(result.stderr).plain.split())


def test_zero_gpus_on_a_server_without_gpus_requests_none(tmp_path: Path) -> None:
    """``--gpu 0`` is the one value a GPU-less Server accepts, and means none."""
    config_path = tmp_path / "config.yaml"
    _save_limited_server(config_path)

    with (
        patch("canfar.models.config.CONFIG_PATH", config_path),
        patch("canfar.cli.create.AsyncSession") as session_cls,
    ):
        session = session_cls.return_value.__aenter__.return_value
        session.create = AsyncMock(return_value=["id-1"])
        result = runner.invoke(
            cli, ["create", "headless", "skaha/worker:v1", "--gpu", "0"]
        )

    assert result.exit_code == 0, result.stderr
    assert session.create.await_args.args[0].gpus is None
