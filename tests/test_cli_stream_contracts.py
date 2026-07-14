"""Public CLI contracts for command data and diagnostics streams."""

from __future__ import annotations

import json
from contextlib import ExitStack
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx
import pytest
import yaml
from typer.testing import CliRunner

from canfar.cli.main import cli
from canfar.errors import (
    ErrorCode,
    LoggingEnvironmentError,
    StructuredError,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from typing import Any

runner = CliRunner()
_CLI_ENV = {"COLUMNS": "120", "NO_COLOR": "1", "FORCE_COLOR": "0", "TERM": "dumb"}
_CADC_REGISTRY = "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps"
_CADC_URI = "ivo://cadc.nrc.ca/skaha"


def _config_path(path: Path) -> ExitStack:
    """Point the CLI and persisted Configuration at a temporary file."""
    stack = ExitStack()
    stack.enter_context(patch("canfar.CONFIG_PATH", path))
    stack.enter_context(patch("canfar.cli.config.CONFIG_PATH", path))
    stack.enter_context(patch("canfar.models.config.CONFIG_PATH", path))
    return stack


def _write_config(path: Path, *, with_server: bool) -> None:
    """Write anonymous X.509 state with optional selected server metadata."""
    server_name = "fresh" if with_server else None
    servers = (
        {
            "fresh": {
                "idp": "cadc",
                "uri": _CADC_URI,
                "url": "https://fresh.example/skaha",
                "version": "v1",
                "auths": ["x509"],
            }
        }
        if with_server
        else {}
    )
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "active": {"authentication": "cadc", "server": server_name},
                "authentication": {
                    "cadc": {"mode": "x509", "path": None, "expiry": 0.0}
                },
                "servers": servers,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _async_client_factory(
    transport: httpx.AsyncBaseTransport,
) -> Callable[..., httpx.AsyncClient]:
    """Return the real HTTPX async client bound to a test transport."""
    client_type = httpx.AsyncClient
    return lambda **kwargs: client_type(transport=transport, **kwargs)


def _client_factory(
    transport: httpx.BaseTransport,
) -> Callable[..., httpx.Client]:
    """Return the real HTTPX client bound to a test transport."""
    client_type = httpx.Client
    return lambda **kwargs: client_type(transport=transport, **kwargs)


@pytest.mark.parametrize(
    ("flags", "load"),
    [
        ([], None),
        (["--json"], json.loads),
        (["--yaml"], yaml.safe_load),
    ],
)
def test_config_success_warning_and_failure_keep_stream_contracts(
    tmp_path: Path,
    flags: list[str],
    load: Callable[[str], Any] | None,
) -> None:
    """Real config outcomes preserve data, diagnostics, and exit semantics."""
    config_path = tmp_path / "missing" / "config.yaml"

    with _config_path(config_path):
        success = runner.invoke(
            cli,
            ["config", "get", "console.width", *flags],
            env=_CLI_ENV,
            color=False,
        )
    assert success.exit_code == 0
    assert success.stderr == ""
    if load is None:
        assert success.stdout.strip().splitlines()[-1] == "120"
    else:
        assert load(success.stdout) == 120
        assert "@" not in success.stdout

    with _config_path(config_path):
        warning = runner.invoke(
            cli,
            ["config", "show", *flags],
            env=_CLI_ENV,
            color=False,
        )
    assert warning.exit_code == 0
    warning_stderr = " ".join(warning.stderr.split())
    assert "does not exist, showing defaults" in warning_stderr
    assert "does not exist, showing defaults" not in " ".join(warning.stdout.split())
    if load is None:
        assert "'version': 1" in warning.stdout
    else:
        payload = load(warning.stdout)
        assert payload["version"] == 1
        assert "@" not in warning.stdout

    with _config_path(config_path):
        failure = runner.invoke(
            cli,
            ["config", "get", "missing.key", *flags],
            env=_CLI_ENV,
            color=False,
        )
    assert failure.exit_code == 1
    if load is None:
        assert "missing.key" in failure.stderr
        assert "missing.key" not in failure.stdout
    else:
        assert failure.stdout == ""
        error = StructuredError.model_validate(load(failure.stderr))
        assert error.code == ErrorCode.COMMAND_VALIDATION_FAILED.value


@pytest.mark.parametrize(
    ("flag", "load"),
    [
        ("--json", json.loads),
        ("--yaml", yaml.safe_load),
    ],
)
def test_real_ps_log_and_payload_stay_on_separate_streams(
    tmp_path: Path,
    flag: str,
    load: Callable[[str], Any],
) -> None:
    """A real HTTP-backed command emits logs beside one machine payload."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, with_server=True)

    def response(request: httpx.Request) -> httpx.Response:
        """Return an empty Session list payload."""
        return httpx.Response(200, json=[], request=request)

    with (
        _config_path(config_path),
        patch(
            "canfar.client.AsyncClient",
            side_effect=_async_client_factory(httpx.MockTransport(response)),
        ),
    ):
        result = runner.invoke(cli, ["-vvvv", "ps", flag])

    assert result.exit_code == 0
    assert load(result.stdout) == []
    assert "Asynchronous HTTPx client created" not in result.stdout
    assert "Asynchronous HTTPx client created" in result.stderr


@pytest.mark.parametrize(
    ("flag", "load"),
    [
        ("--json", json.loads),
        ("--yaml", yaml.safe_load),
    ],
)
def test_ps_transport_failure_is_one_structured_machine_error(
    tmp_path: Path,
    flag: str,
    load: Callable[[str], Any],
) -> None:
    """Expected HTTP transport failure preserves empty stdout and exit one."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, with_server=True)

    def unavailable(request: httpx.Request) -> httpx.Response:
        """Simulate a refused Session list request."""
        message = "connection refused"
        raise httpx.ConnectError(message, request=request)

    with (
        _config_path(config_path),
        patch(
            "canfar.client.AsyncClient",
            side_effect=_async_client_factory(httpx.MockTransport(unavailable)),
        ),
    ):
        result = runner.invoke(cli, ["ps", flag])

    assert result.exit_code == 1
    assert result.stdout == ""
    error = StructuredError.model_validate(load(result.stderr))
    assert error.code == ErrorCode.TRANSPORT_FAILURE.value


@pytest.mark.parametrize(
    ("flag", "load"),
    [
        ("--json", json.loads),
        ("--yaml", yaml.safe_load),
    ],
)
def test_fresh_server_discovery_keeps_progress_out_of_machine_payload(
    tmp_path: Path,
    flag: str,
    load: Callable[[str], Any],
) -> None:
    """Fresh registry discovery emits progress on stderr and data on stdout."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, with_server=False)
    registry_body = f"{_CADC_URI}=https://fresh.example/skaha/capabilities"

    def registry_response(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and str(request.url) == _CADC_REGISTRY:
            return httpx.Response(200, text=registry_body, request=request)
        if request.method == "HEAD":
            return httpx.Response(200, request=request)
        message = f"Unexpected request: {request.method} {request.url}"
        raise AssertionError(message)

    capabilities = """
        <capabilities>
          <capability standardID="http://www.opencadc.org/std/platform#session-2">
            <interface>
              <accessURL use="base">https://fresh.example/skaha/v1</accessURL>
              <securityMethod
                standardID="ivo://ivoa.net/sso#tls-with-certificate"
              />
            </interface>
          </capability>
        </capabilities>
    """

    def capability_response(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=capabilities, request=request)

    discovery_httpx = SimpleNamespace(
        AsyncClient=_async_client_factory(httpx.MockTransport(registry_response)),
        HTTPError=httpx.HTTPError,
        Timeout=httpx.Timeout,
    )
    with (
        _config_path(config_path),
        patch("canfar.utils.discover.httpx", discovery_httpx),
        patch(
            "canfar.client.Client",
            side_effect=_client_factory(httpx.MockTransport(capability_response)),
        ),
    ):
        result = runner.invoke(cli, ["server", "ls", flag])

    assert result.exit_code == 0, result.stderr
    payload = load(result.stdout)
    assert [item["name"] for item in payload] == ["canfar"]
    assert "Fetched CADC" not in result.stdout
    assert "Fetched CADC" in result.stderr


def test_fresh_server_discovery_errors_are_diagnostics(
    tmp_path: Path,
) -> None:
    """Human discovery failure is rendered once at the command boundary."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, with_server=False)

    def unavailable(request: httpx.Request) -> httpx.Response:
        message = "registry unavailable"
        raise httpx.ConnectError(message, request=request)

    with (
        _config_path(config_path),
        patch(
            "canfar.utils.discover.httpx.AsyncClient",
            side_effect=_async_client_factory(httpx.MockTransport(unavailable)),
        ),
    ):
        result = runner.invoke(cli, ["server", "ls"])

    assert result.exit_code == 1
    assert "Failed to fetch CADC" not in result.stdout
    assert "Failed to fetch CADC" not in result.stderr
    assert result.stderr.count("Failed to discover servers for IDP") == 1


@pytest.mark.parametrize(
    ("flag", "load"),
    [
        ("--json", json.loads),
        ("--yaml", yaml.safe_load),
    ],
)
def test_fresh_server_discovery_failure_is_one_structured_machine_error(
    tmp_path: Path,
    flag: str,
    load: Callable[[str], Any],
) -> None:
    """Registry transport failure emits one machine-readable boundary error."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, with_server=False)

    def unavailable(request: httpx.Request) -> httpx.Response:
        message = "registry unavailable"
        raise httpx.ConnectError(message, request=request)

    with (
        _config_path(config_path),
        patch(
            "canfar.utils.discover.httpx.AsyncClient",
            side_effect=_async_client_factory(httpx.MockTransport(unavailable)),
        ),
    ):
        result = runner.invoke(cli, ["server", "ls", flag])

    assert result.exit_code == 1
    assert result.stdout == ""
    error = StructuredError.model_validate(load(result.stderr))
    assert error.code == ErrorCode.SERVER_DISCOVERY_FAILED.value


@pytest.mark.parametrize(
    "command",
    [
        ["config", "get", "console.width", "--json"],
        ["auth", "show", "--json"],
        ["auth", "ls", "--json"],
        ["server", "ls", "--json"],
        ["ps", "--json"],
    ],
)
def test_malformed_config_is_structured_for_every_machine_command(
    tmp_path: Path,
    command: list[str],
) -> None:
    """Every machine-capable command reports reset-required state uniformly."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("version: 0\n", encoding="utf-8")

    with _config_path(config_path):
        result = runner.invoke(cli, command)

    assert result.exit_code == 1
    assert result.stdout == ""
    error = StructuredError.model_validate(json.loads(result.stderr))
    assert error.code == ErrorCode.CONFIG_INVALID.value


@pytest.mark.parametrize(
    ("flag", "load"),
    [
        ("--json", json.loads),
        ("--yaml", yaml.safe_load),
    ],
)
def test_invalid_logging_environment_is_one_structured_machine_error(
    monkeypatch: pytest.MonkeyPatch,
    flag: str,
    load: Callable[[str], Any],
) -> None:
    """Root dispatch preserves parsed leaf args for callback setup failures."""
    monkeypatch.setenv("CANFAR_LOGLEVEL", "chatty")

    result = runner.invoke(cli, ["config", "get", "console.width", flag])

    assert result.exit_code == 2
    assert result.stdout == ""
    error = LoggingEnvironmentError.model_validate(load(result.stderr))
    assert error.code == ErrorCode.LOGGING_INVALID_ENV_VALUE.value
    assert error.env_var == "CANFAR_LOGLEVEL"
    assert error.provided_value == "chatty"
    assert error.expected == ["critical", "error", "warning", "info", "debug"]


def test_relative_log_file_creates_parents_without_contaminating_stdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The root file sink resolves from CWD and keeps machine output data-only."""
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        cli,
        [
            "--log-file",
            "nested/logs/canfar.jsonl",
            "config",
            "get",
            "console.width",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert json.loads(result.stdout) == 120
    assert result.stderr == ""
    assert (tmp_path / "nested/logs/canfar.jsonl").is_file()


@pytest.mark.parametrize(("target", "directory"), [("-", False), ("logs", True)])
@pytest.mark.parametrize(
    ("flag", "load"),
    [(None, None), ("--json", json.loads), ("--yaml", yaml.safe_load)],
)
def test_invalid_log_file_target_is_a_structured_setup_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
    directory: bool,
    flag: str | None,
    load: Callable[[str], Any] | None,
) -> None:
    """Directory and pseudo-file targets fail at the existing setup boundary."""
    monkeypatch.chdir(tmp_path)
    if directory:
        (tmp_path / target).mkdir()
    args = ["--log-file", target, "config", "get", "console.width"]
    if flag:
        args.append(flag)

    result = runner.invoke(cli, args)

    assert result.exit_code == 2
    assert result.stdout == ""
    if load is None:
        assert ErrorCode.LOGGING_INVALID_FILE_PATH.value in result.stderr
    else:
        error = StructuredError.model_validate(load(result.stderr))
        assert error.code == ErrorCode.LOGGING_INVALID_FILE_PATH.value


@pytest.mark.parametrize(
    ("flag", "load"),
    [(None, None), ("--json", json.loads), ("--yaml", yaml.safe_load)],
)
def test_log_file_initialization_failure_keeps_command_running(
    tmp_path: Path,
    flag: str | None,
    load: Callable[[str], Any] | None,
) -> None:
    """An unavailable sink emits one mode-aware structured warning."""
    log_file = tmp_path / "unavailable.jsonl"
    args = ["--log-file", str(log_file), "config", "get", "console.width"]
    if flag:
        args.append(flag)

    with patch(
        "logging.handlers.RotatingFileHandler.__init__",
        side_effect=OSError("synthetic sink failure"),
    ):
        result = runner.invoke(cli, args)

    assert result.exit_code == 0, result.stderr
    if load is None:
        assert result.stdout.rstrip().endswith("120")
        assert result.stderr.count(ErrorCode.LOGGING_FILE_SINK_UNAVAILABLE.value) == 1
    else:
        assert load(result.stdout) == 120
        error = StructuredError.model_validate(load(result.stderr))
        assert error.code == ErrorCode.LOGGING_FILE_SINK_UNAVAILABLE.value
    assert not log_file.exists()
