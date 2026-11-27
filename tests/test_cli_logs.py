"""Tests for the logs CLI module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx2
import pytest
from typer.testing import CliRunner

from canfar.cli.main import cli
from canfar.exceptions.session import SessionRequestError

runner = CliRunner()


def _mock_async_session(mock_session_cls: MagicMock) -> AsyncMock:
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session
    return mock_session


def test_logs_outputs_logs_and_empty_message() -> None:
    """Test logs command output and empty result message."""
    with patch("canfar.cli.logs.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.logs.return_value = {"abc": "hello\nworld"}
        result = runner.invoke(cli, ["logs", "abc"])

    assert result.exit_code == 0
    assert "Logs for session abc" in result.stdout
    assert "hello" in result.stdout

    with patch("canfar.cli.logs.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.logs.return_value = {}
        result = runner.invoke(cli, ["logs", "abc"])

    assert result.exit_code == 0
    assert "No logs found" in result.stderr


def test_logs_reports_fetch_error() -> None:
    """Test logs command reports fetch errors."""
    with patch("canfar.cli.logs.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.logs.side_effect = RuntimeError("boom")
        result = runner.invoke(cli, ["logs", "abc"])

    assert result.exit_code == 1
    assert "Could not fetch logs" not in result.stdout
    assert "boom" not in result.stdout
    assert "Could not fetch logs" in result.stderr
    assert "boom" in result.stderr


@pytest.mark.parametrize(
    ("log_text", "expected"),
    [
        pytest.param(
            "[bold]progress[/bold]\nhello world",
            "progress\nhello world",
            id="valid-markup",
        ),
        pytest.param(
            "[bold]progress[/bold]\n"
            "SynthesisImagerVi2::defineImage Define image coordinates for "
            "[/arc/projects/foo/bar]",
            "[bold]progress[/bold]\n"
            "SynthesisImagerVi2::defineImage Define image coordinates for "
            "[/arc/projects/foo/bar]",
            id="casa-literal-fallback",
        ),
    ],
)
def test_logs_renders_once_with_markup_fallback(log_text: str, expected: str) -> None:
    """Render markup or fall back to literal text without partial or duplicate logs."""
    with patch("canfar.cli.logs.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.logs.return_value = {"abc": log_text}
        result = runner.invoke(cli, ["logs", "abc"])

    assert result.exit_code == 0, result.exception
    assert result.stdout.count("Logs for session abc") == 1
    assert "[bold magenta]" not in result.stdout
    assert result.stdout.count(expected) == 1
    assert result.stdout.endswith(f"{expected}\n")
    assert result.stdout.count("progress") == 1
    session.logs.assert_awaited_once_with(ids=["abc"], replica=None)


def test_logs_passes_the_replica_index() -> None:
    """``--replica`` reaches the library as the batch replica index."""
    with patch("canfar.cli.logs.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.logs.return_value = {"k7nq2wpx": "replica one"}
        result = runner.invoke(cli, ["logs", "k7nq2wpx", "--replica", "1"])

    assert result.exit_code == 0
    assert "replica one" in result.stdout
    session.logs.assert_awaited_once_with(ids=["k7nq2wpx"], replica=1)


def test_logs_reports_the_server_rejection_and_exits_one() -> None:
    """A rejected log request prints the Server's 400 after the other logs."""
    request = httpx2.Request("GET", "https://example.test/session/k7nq2wpx")
    response = httpx2.Response(
        400, text='{"message": "replica is required"}', request=request
    )
    error = httpx2.HTTPStatusError("400", request=request, response=response)
    with patch("canfar.cli.logs.AsyncSession") as session_cls:
        session = _mock_async_session(session_cls)
        session.logs.side_effect = SessionRequestError(
            "logs", {"abc": "hello"}, {"k7nq2wpx": error}
        )
        result = runner.invoke(cli, ["logs", "abc", "k7nq2wpx"])

    assert result.exit_code == 1
    assert "hello" in result.stdout
    assert "HTTP 400" in result.stderr
    assert "replica is required" in result.stderr
    assert "No logs found" not in result.stderr
