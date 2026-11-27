"""``canfar registry`` and ``canfar create --private`` at the CLI seam."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx2
import pytest
import yaml
from typer.testing import CliRunner

from canfar.cli.main import cli

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

runner = CliRunner()
_SECRET = "harbor-s3cret"
_IMAGE = "images.canfar.net/lisa-ddpc/protolab:latest"
_HEADER = "X-Skaha-Registry-Auth"


@pytest.fixture
def config_path(tmp_path: Path) -> Iterator[Path]:
    """Isolated configuration file path."""
    path = tmp_path / "config.yaml"
    with patch("canfar.models.config.CONFIG_PATH", path):
        yield path


def _login(*args: str, secret: str = _SECRET):
    return runner.invoke(
        cli,
        ["registry", "login", *args, "-u", "ada", "--secret-stdin"],
        input=f"{secret}\n",
    )


def test_login_saves_by_host_and_never_echoes_the_secret(
    config_path: Path, tmp_path: Path
) -> None:
    """Login stores the credential under its host with the file kept 0600."""
    log_file = tmp_path / "canfar.jsonl"
    result = runner.invoke(
        cli,
        [
            "-vv",
            "--log-file",
            str(log_file),
            "registry",
            "login",
            "https://Images.Canfar.Net/",
            "-u",
            "ada",
            "--secret-stdin",
        ],
        input=f"{_SECRET}\n",
    )

    assert result.exit_code == 0, result.output
    _before, marker, after = result.stdout.partition("Saved credential for ")
    shown_host, _as_label, _rest = after.partition(" as ")
    assert marker
    assert shown_host == "images.canfar.net"
    assert _SECRET not in result.output
    assert not log_file.exists() or _SECRET not in log_file.read_text("utf-8")
    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert saved["registries"] == {
        "images.canfar.net": {"username": "ada", "secret": _SECRET}
    }
    assert config_path.stat().st_mode & 0o777 == 0o600


def test_login_without_a_terminal_or_stdin_secret_fails_before_saving(
    config_path: Path,
) -> None:
    """No TTY and no --secret-stdin, or no username, fails without a prompt."""
    no_secret = runner.invoke(cli, ["registry", "login", "-u", "ada"])
    no_username = runner.invoke(
        cli, ["registry", "login", "--secret-stdin"], input=f"{_SECRET}\n"
    )
    empty = _login(secret="")

    assert no_secret.exit_code == 1
    assert "--secret-stdin" in no_secret.stderr
    assert no_username.exit_code == 1
    assert "--username" in no_username.stderr
    assert empty.exit_code == 1
    assert not config_path.exists()


def test_ls_shows_host_username_and_source_without_secrets(
    config_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Saved and env credentials list with their source; secrets never print."""
    assert _login("harbor.example:5000").exit_code == 0
    monkeypatch.setenv("CANFAR_REGISTRY__USERNAME", "robot-ci")
    monkeypatch.setenv("CANFAR_REGISTRY__SECRET", "env-s3cret")

    machine = runner.invoke(cli, ["registry", "ls", "-o", "json"])
    human = runner.invoke(cli, ["registry", "ls"])

    assert machine.exit_code == 0, machine.output
    assert json.loads(machine.stdout) == [
        {"host": "harbor.example:5000", "username": "ada", "source": "saved"},
        {"host": "*", "username": "robot-ci", "source": "env"},
    ]
    assert human.exit_code == 0
    assert "harbor.example:5000" in human.stdout
    assert "robot-ci" in human.stdout
    for result in (machine, human):
        assert _SECRET not in result.output
        assert "env-s3cret" not in result.output
    assert "env-s3cret" not in config_path.read_text(encoding="utf-8")


def test_logout_removes_one_host_and_repeats_cleanly(config_path: Path) -> None:
    """Logout drops only its host, and a second logout still exits 0."""
    assert _login().exit_code == 0
    assert _login("harbor.example").exit_code == 0

    first = runner.invoke(cli, ["registry", "logout"])
    again = runner.invoke(cli, ["registry", "logout"])

    assert first.exit_code == 0
    assert again.exit_code == 0
    assert "Not logged in to images.canfar.net." in again.stdout
    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert list(saved["registries"]) == ["harbor.example"]


def _sessions(seen: list[httpx2.Request]):
    def respond(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        name = request.url.params.get("name", "session")
        return httpx2.Response(200, text=f"{name}-id\n", request=request)

    real_client = httpx2.AsyncClient
    return patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kw: real_client(
            transport=httpx2.MockTransport(respond), **kw
        ),
    )


@pytest.fixture
def runtime_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the CLI at a mock Science Platform with a runtime token."""
    monkeypatch.setenv("CANFAR_TOKEN", "test-token")
    monkeypatch.setenv("CANFAR_URL", "https://example.test/skaha/v1/")


@pytest.mark.usefixtures("config_path", "runtime_server")
@pytest.mark.parametrize("private", [True, False])
def test_create_sends_registry_auth_only_with_private(private: bool) -> None:
    """Every replica POST carries the saved credential only under --private."""
    assert _login().exit_code == 0
    seen: list[httpx2.Request] = []
    flags = ["--private"] if private else []
    with _sessions(seen):
        result = runner.invoke(
            cli, ["create", "headless", _IMAGE, "-r", "3", "-o", "json", *flags]
        )

    assert result.exit_code == 0, result.output
    assert len(json.loads(result.stdout)) == 3
    expected = base64.b64encode(f"ada:{_SECRET}".encode()).decode()
    assert [request.method for request in seen] == ["POST"] * 3
    assert [request.headers.get(_HEADER) for request in seen] == (
        [expected] * 3 if private else [None] * 3
    )
    assert _SECRET not in result.output
    assert expected not in result.output


@pytest.mark.usefixtures("runtime_server")
@pytest.mark.parametrize(
    "mode",
    [[], ["-o", "json"], ["-o", "yaml"], ["--dry-run"]],
    ids=["human", "json", "yaml", "dry-run"],
)
def test_private_create_without_credential_fails(
    config_path: Path, mode: list[str]
) -> None:
    """A private launch with no credential fails before any request."""
    seen: list[httpx2.Request] = []
    with _sessions(seen):
        result = runner.invoke(cli, ["create", "headless", _IMAGE, "--private", *mode])

    assert result.exit_code == 1, result.output
    assert seen == []
    assert "canfar registry login images.canfar.net" in result.stderr
    assert "CANFAR_REGISTRY__USERNAME" in result.stderr
    assert not config_path.exists()


@pytest.mark.usefixtures("config_path")
def test_private_short_name_fails_without_rewrite() -> None:
    """``skaha/astroml --private`` is a usage error that names the full image."""
    result = runner.invoke(
        cli, ["create", "headless", "skaha/astroml", "--private", "--dry-run"]
    )

    assert result.exit_code == 1
    assert "HOST/PROJECT/IMAGE" in result.stderr
    assert "images.canfar.net/skaha/astroml:latest" in result.stderr
    assert "Resolved image" not in result.stdout


@pytest.mark.usefixtures("config_path")
def test_private_dry_run_checks_the_credential_and_hides_it() -> None:
    """Dry run prints the resolved private image, never the secret or header."""
    assert _login().exit_code == 0
    result = runner.invoke(
        cli, ["create", "headless", _IMAGE, "--private", "--dry-run"]
    )

    assert result.exit_code == 0, result.output
    assert f"Resolved image: {_IMAGE}" in result.stdout
    assert "Private: True" in result.stdout
    assert _SECRET not in result.output
    assert base64.b64encode(f"ada:{_SECRET}".encode()).decode() not in result.output


@pytest.mark.usefixtures("config_path", "runtime_server")
@pytest.mark.parametrize(
    ("flags", "hint"),
    [
        ([], "rerun with --private"),
        (["--private"], "canfar registry ls"),
    ],
    ids=["public", "private"],
)
def test_empty_create_hint_mentions_private(flags: list[str], hint: str) -> None:
    """With no IDs returned, the hint points at --private or the credential."""
    assert _login().exit_code == 0
    real_client = httpx2.AsyncClient
    transport = httpx2.MockTransport(
        lambda request: httpx2.Response(503, request=request)
    )
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kw: real_client(transport=transport, **kw),
    ):
        result = runner.invoke(
            cli, ["create", "headless", _IMAGE, "-o", "json", *flags]
        )

    assert result.exit_code == 1
    error = json.loads(result.stderr)
    assert error["code"] == "transport.failure"
    assert hint in error["hint"]
