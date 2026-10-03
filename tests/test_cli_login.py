"""Tests for the top-level ``canfar login`` CLI command."""

from __future__ import annotations

import re
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
import yaml
from pydantic import AnyHttpUrl, AnyUrl
from rich.console import Console
from rich.logging import RichHandler
from typer.testing import CliRunner

from canfar.auth import x509
from canfar.cli.login import _live_output
from canfar.cli.main import cli
from canfar.errors import ErrorCode
from canfar.models.auth import X509Credential
from canfar.models.config import Configuration
from canfar.models.http import Server
from canfar.models.registry import ServerProbe
from canfar.server import ServerDiscoveryError
from tests.test_auth_x509 import generate_cert

if TYPE_CHECKING:
    from collections.abc import Callable

runner = CliRunner()
_CADC_URI = "ivo://cadc.nrc.ca/skaha"


def _patch_config(path: Path):
    return patch.multiple(
        "canfar",
        CONFIG_PATH=path,
    )


def _write_config(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data), encoding="utf-8")


def _merge_servers(config: Configuration, discovered: list[Server], idp: str) -> None:  # noqa: ARG001
    for server in discovered:
        if server.name is not None:
            config.servers[server.name] = server


def test_login_help_is_available() -> None:
    """Top-level login exposes help text."""
    result = runner.invoke(cli, ["login", "--help"])
    assert result.exit_code == 0
    assert "Login to CANFAR Science Platform" in result.stdout


@pytest.mark.parametrize(
    "arguments",
    [["login", "cadc"]],
    ids=["canonical"],
)
def test_login_defaults_to_ten_second_timeout(arguments: list[str]) -> None:
    """The canonical login command defaults to ten seconds."""
    with patch("canfar.cli.login._login_flow") as login_flow:
        result = runner.invoke(cli, arguments)

    assert result.exit_code == 0
    login_flow.assert_called_once_with("cadc", force=False, dev=False, timeout=10)


def test_login_without_config_file_does_not_require_force(tmp_path: Path) -> None:
    """Default in-memory credentials do not block first login."""
    config_path = tmp_path / "config.yaml"
    credential = X509Credential(
        idp="cadc",
        path=Path("/new/cert.pem"),
        expiry=456.0,
    )
    discovered = [
        Server(
            idp="cadc",
            name="CADC-CANFAR",
            uri=AnyUrl(_CADC_URI),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
            version="v1",
            auths=["x509"],
        )
    ]
    validated = discovered[0].model_copy(deep=True)

    with (
        _patch_config(config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
        patch("canfar.cli.login.authenticate_for_cli", return_value=credential),
        patch("canfar.server._validate_server", return_value=validated),
        patch(
            "canfar.cli.login.discover",
            side_effect=lambda idp, *, config, **_kwargs: (
                _merge_servers(
                    config,
                    discovered,
                    idp,
                )
                or discovered
            ),
        ),
    ):
        result = runner.invoke(cli, ["login", "cadc"])

    assert result.exit_code == 0
    assert "already exists" not in result.stdout


def test_login_saves_auth_and_server_atomically(tmp_path: Path) -> None:
    """Login persists active Authentication and Server in one save."""
    config_path = tmp_path / "config.yaml"
    credential = X509Credential(
        idp="cadc",
        path=Path("/new/cert.pem"),
        expiry=456.0,
    )
    discovered = [
        Server(
            idp="cadc",
            name="CADC-CANFAR",
            uri=AnyUrl(_CADC_URI),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
            version="v1",
            auths=["x509"],
        )
    ]
    validated = discovered[0].model_copy(deep=True)

    with (
        _patch_config(config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
        patch("canfar.cli.login.authenticate_for_cli", return_value=credential),
        patch("canfar.server._validate_server", return_value=validated),
        patch(
            "canfar.cli.login.discover",
            side_effect=lambda idp, *, config, **_kwargs: (
                _merge_servers(
                    config,
                    discovered,
                    idp,
                )
                or discovered
            ),
        ),
    ):
        result = runner.invoke(cli, ["login", "cadc", "--force"])

    assert result.exit_code == 0
    with patch("canfar.models.config.CONFIG_PATH", config_path):
        saved = Configuration()
    assert saved.active.authentication == "cadc"
    assert saved.active.server == "CADC-CANFAR"
    assert saved.authentication["cadc"].path == Path("/new/cert.pem")


def test_login_passes_dev_and_timeout_to_http_steps(tmp_path: Path) -> None:
    """Login --dev and --timeout flow into auth, discovery, and validation."""
    config_path = tmp_path / "config.yaml"
    credential = X509Credential(
        idp="cadc",
        path=Path("/new/cert.pem"),
        expiry=456.0,
    )
    discovered = [
        Server(
            idp="cadc",
            name="CADC-CANFAR",
            uri=AnyUrl(_CADC_URI),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
            version="v1",
            auths=["x509"],
        )
    ]
    validated = discovered[0].model_copy(deep=True)
    authenticate = MagicMock(return_value=credential)
    validate = MagicMock(return_value=validated)

    def discover(
        idp: str,
        *,
        config: Configuration,
        dev: bool,
        timeout: int,
        save: bool,
        on_probe: Callable[[ServerProbe], None],
    ) -> list[Server]:
        assert idp == "cadc"
        assert dev is True
        assert timeout == 9
        assert save is False
        assert callable(on_probe)
        _merge_servers(config, discovered, idp)
        return discovered

    with (
        _patch_config(config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
        patch("canfar.cli.login.authenticate_for_cli", authenticate),
        patch("canfar.server._validate_server", validate),
        patch("canfar.cli.login.discover", side_effect=discover),
    ):
        result = runner.invoke(
            cli,
            ["login", "cadc", "--force", "--dev", "--timeout", "9"],
        )

    assert result.exit_code == 0
    authenticate.assert_called_once()
    assert authenticate.call_args.kwargs["timeout"] == 9
    assert authenticate.call_args.kwargs["force"] is True
    validate.assert_called_once()
    validated = validate.call_args.args[0]
    assert str(validated.uri) == _CADC_URI
    assert validate.call_args.kwargs["idp"] == "cadc"
    assert validate.call_args.kwargs["timeout"] == 9
    assert isinstance(validate.call_args.kwargs["config"], Configuration)


@pytest.mark.parametrize("expired", [False, True])
def test_login_existing_cadc_reuses_or_reauthenticates(
    tmp_path: Path, expired: bool
) -> None:
    """A saved record permits certificate reuse or interactive re-authentication."""
    config_path = tmp_path / "config.yaml"
    certificate = tmp_path / "cert.pem"
    generate_cert(certificate, expired=expired)
    inspect_certificate = x509.inspect

    def acquire_certificate() -> dict:
        generate_cert(certificate)
        return inspect_certificate(certificate)

    _write_config(
        config_path,
        {
            "version": 1,
            "active": {"authentication": "cadc", "server": "CADC-CANFAR"},
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": str(certificate),
                    "expiry": 1.0,
                }
            },
            "servers": {
                "CADC-CANFAR": {
                    "idp": "cadc",
                    "uri": _CADC_URI,
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                }
            },
        },
    )
    selected = Server(
        idp="cadc",
        name="CADC-CANFAR",
        uri=AnyUrl(_CADC_URI),
        url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
        version="v1",
        auths=["x509"],
    )

    with (
        _patch_config(config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
        patch(
            "canfar.auth.x509.inspect",
            side_effect=lambda: inspect_certificate(certificate),
        ),
        patch("canfar.auth.x509.gather", side_effect=acquire_certificate) as gather,
        patch("canfar.cli.login.discover", return_value=[selected]),
        patch("canfar.server._validate_server", return_value=selected),
    ):
        result = runner.invoke(cli, ["login", "cadc"])
        saved = Configuration()

    assert result.exit_code == 0, result.output
    assert gather.call_count == int(expired)
    assert (
        saved.authentication["cadc"].expiry
        == inspect_certificate(certificate)["expiry"]
    )
    assert saved.active.authentication == "cadc"
    assert saved.active.server == "CADC-CANFAR"


@pytest.mark.parametrize("existing", [False, True])
def test_login_presents_device_flow_failure_on_terminal(
    tmp_path: Path, existing: bool
) -> None:
    """Device login runs with a saved record and preserves it on failure."""
    config_path = tmp_path / "config.yaml"
    if existing:
        _write_config(
            config_path,
            {
                "version": 1,
                "active": {"authentication": "srcnet", "server": None},
                "authentication": {"srcnet": {"mode": "oidc"}},
            },
        )
    original = config_path.read_bytes() if existing else None

    with (
        _patch_config(config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
        patch(
            "canfar.cli.login.authenticate_for_cli",
            side_effect=PermissionError("OIDC device authorization was denied"),
        ),
    ):
        result = runner.invoke(cli, ["login", "srcnet"])

    assert result.exit_code == 1
    assert "OIDC device authorization was denied" in result.stderr
    assert (config_path.read_bytes() if config_path.exists() else None) == original


def _probe(name: str, status: str) -> ServerProbe:
    return ServerProbe(
        name=name,
        uri=f"ivo://{name}.example/skaha",
        url=f"https://{name}.example/skaha",
        status=status,
    )


def _login_with_outcomes(
    tmp_path: Path,
    outcomes: list[ServerProbe],
    *,
    root: tuple[str, ...] = (),
    options: tuple[str, ...] = (),
    error: ServerDiscoveryError | None = None,
):
    """Log in while fake discovery reports ``outcomes``; return the result.

    Discovery raises ``error``, or the no-Server error when nothing connected.
    """
    config_path = tmp_path / "config.yaml"
    credential = X509Credential(idp="cadc", path=Path("/new/cert.pem"), expiry=456.0)
    discovered = [
        Server(
            idp="cadc",
            name="canSRC",
            uri=AnyUrl("ivo://canSRC.example/skaha"),
            url=AnyHttpUrl("https://canSRC.example/skaha"),
            version="v1",
            auths=["x509"],
        )
    ]

    def discover(idp: str, *, config: Configuration, on_probe, **_kwargs):
        for probe in outcomes:
            on_probe(probe)
        if error is not None:
            raise error
        if not any(probe.status == "connected" for probe in outcomes):
            message = f"No servers discovered for IDP '{idp}'."
            raise ServerDiscoveryError(message, code=ErrorCode.SERVER_NONE_AVAILABLE)
        _merge_servers(config, discovered, idp)
        return discovered

    with (
        _patch_config(config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
        patch("canfar.cli.login.authenticate_for_cli", return_value=credential),
        patch("canfar.server._validate_server", return_value=discovered[0]),
        patch("canfar.cli.login.discover", side_effect=discover),
    ):
        return runner.invoke(cli, [*root, "login", "cadc", *options])


_OUTCOMES = [
    *(
        _probe(name, "pending")
        for name in ("ukRAL", "canSRC", "cnSRC", "krSRC", "canSRC")
    ),
    _probe("ukRAL", "timeout"),
    _probe("canSRC", "connected"),
    _probe("cnSRC", "unreachable"),
    _probe("krSRC", "error"),
    _probe("canSRC", "error"),
]
"""Pending reports, then one outcome each; ``canSRC`` is listed twice."""


def test_login_shows_discovery_squares_legend_and_timeout_hint(
    tmp_path: Path,
) -> None:
    """Login shows one glyph per Server, a legend, and how to wait longer.

    CliRunner stderr has no color, so each state uses its plain glyph.
    """
    result = _login_with_outcomes(tmp_path, _OUTCOMES)

    assert result.exit_code == 0
    assert result.stderr.strip().splitlines()[-4:-2] == [
        "+ x ! ~",
        "+ 1 discovered   ~ 1 timeout   x 1 unreachable   ! 1 failed",
    ]
    summary, hint = result.stderr.strip().splitlines()[-2:]
    assert re.fullmatch(
        r"Checked 4 servers in \d+\.\ds with a 10s request timeout\.", summary
    )
    assert hint == "1 timed out. To wait longer, run canfar login cadc --timeout 20"
    assert "canSRC" not in result.stderr
    assert "Fetched" not in result.stderr
    assert "Login completed successfully" in result.stdout


@pytest.mark.parametrize(
    ("options", "hint"),
    [
        (("--dev", "--timeout", "9"), "run canfar login cadc --dev --timeout 18"),
        (("--timeout", "200"), "run canfar login cadc --timeout 300"),
        (("--timeout", "300"), None),
    ],
    ids=["keeps-dev", "caps-at-300", "already-at-limit"],
)
def test_login_timeout_hint_repeats_scope_and_respects_the_limit(
    tmp_path: Path,
    options: tuple[str, ...],
    hint: str | None,
) -> None:
    """The suggested command keeps --dev and never exceeds the client limit."""
    result = _login_with_outcomes(tmp_path, _OUTCOMES, options=options)

    assert result.exit_code == 0
    last = result.stderr.strip().splitlines()[-1]
    if hint is None:
        assert last.startswith("Checked 4 servers in ")
    else:
        assert last.endswith(hint)


@pytest.mark.parametrize(
    ("root", "named"),
    [
        (("--log-level", "info"), True),
        (("-vvv",), True),
        (("--log-level", "warning"), False),
    ],
    ids=["info", "-vvv", "warning"],
)
def test_login_names_discovered_servers_from_info_logging(
    tmp_path: Path,
    root: tuple[str, ...],
    named: bool,
) -> None:
    """INFO or more verbose logging labels each glyph with its Server Name."""
    result = _login_with_outcomes(tmp_path, _OUTCOMES, root=root)

    assert result.exit_code == 0
    labelled = [
        "+", "canSRC", "x", "cnSRC", "!", "krSRC", "~", "ukRAL",
    ]  # fmt: skip
    assert (labelled in [line.split() for line in result.stderr.splitlines()]) is named


def test_login_shows_discovery_outcomes_before_no_server_error(
    tmp_path: Path,
) -> None:
    """When no Server connects, the grid still explains each failure."""
    result = _login_with_outcomes(
        tmp_path, [_probe("ukRAL", "pending"), _probe("ukRAL", "unreachable")]
    )

    assert result.exit_code == 1
    lines = result.stderr.strip().splitlines()
    assert lines[-5:-3] == [
        "x",
        "+ 0 discovered   ~ 0 timeout   x 1 unreachable   ! 0 failed",
    ]
    assert lines[-3].startswith("Checked 1 server in ")
    assert lines[-2:] == ["", "No servers discovered for IDP 'cadc'."]


def test_login_registry_failure_suggests_network_check_or_longer_timeout(
    tmp_path: Path,
) -> None:
    """A registry that cannot be read gets advice instead of an empty grid."""
    error = ServerDiscoveryError(
        "Failed to discover servers for IDP 'cadc': CADC: timed out"
    )

    result = _login_with_outcomes(tmp_path, [], error=error)

    assert result.exit_code == 1
    assert result.stderr.strip().splitlines()[-2:] == [
        "Failed to discover servers for IDP 'cadc': CADC: timed out",
        (
            "Check your network connection, or if the registry is slow, run "
            "canfar login cadc --timeout 20"
        ),
    ]


def test_live_output_routes_logs_and_restores_console(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Log records print through the live console, which then reverts."""
    live = Console(file=StringIO(), width=120, force_terminal=True)
    original = Console(file=StringIO())
    handler = RichHandler(console=original)
    monkeypatch.setattr("canfar.utils.logging._rich_handler", handler)
    monkeypatch.setattr("canfar.cli.login.Console", lambda **_kwargs: Console(width=72))

    with _live_output(live):
        assert handler.console is live
        assert live.width == 72

    assert handler.console is original
    assert live.width == 120
