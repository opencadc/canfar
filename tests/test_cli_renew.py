"""Tests for the renew CLI module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx2
from typer.testing import CliRunner

from canfar.cli.main import cli

runner = CliRunner()


def _mock_async_session(mock_session_cls: MagicMock) -> AsyncMock:
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session
    return mock_session


def test_renew_success_and_failure() -> None:
    """Test successful renewal, partial failure, and unhandled exception."""
    with patch("canfar.cli.renew.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.renew.return_value = {"abc": True}
        result = runner.invoke(cli, ["renew", "abc"])

    assert result.exit_code == 0
    assert "Successfully renewed 1 session(s)." in result.stdout

    with patch("canfar.cli.renew.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.renew.return_value = {"abc": True, "def": False}
        result = runner.invoke(cli, ["renew", "abc", "def"])

    assert result.exit_code == 0
    assert "Successfully renewed 1 session(s)." in result.stdout
    assert "Failed to renew 1 session(s): def" in result.stderr

    with patch("canfar.cli.renew.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.renew.side_effect = RuntimeError("network down")
        result = runner.invoke(cli, ["renew", "abc"])

    assert result.exit_code == 0
    assert "Error during renewal: network down" in result.stderr


def test_renew_summary_ignores_errors_environment(monkeypatch) -> None:
    """CANFAR_ERRORS=raise does not change the CLI's renewal summary."""
    monkeypatch.setenv("CANFAR_ERRORS", "raise")
    monkeypatch.setenv("CANFAR_TOKEN", "token")
    monkeypatch.setenv("CANFAR_URL", "https://example.test/skaha/v1")

    def respond(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(500 if request.url.path.endswith("/def") else 200)

    real_async_client = httpx2.AsyncClient
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx2.MockTransport(respond), **kwargs
        ),
    ):
        result = runner.invoke(cli, ["renew", "abc", "def"])

    assert "Successfully renewed 1 session(s)." in result.stdout
    assert "Failed to renew 1 session(s): def" in result.stderr


def test_renew_without_arguments_shows_help() -> None:
    """Calling renew without arguments shows help and exits with error."""
    result = runner.invoke(cli, ["renew"])
    assert result.exit_code != 0
