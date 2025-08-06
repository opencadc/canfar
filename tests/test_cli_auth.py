"""Tests for the `skaha auth` CLI commands."""

from typer.testing import CliRunner

from skaha.cli.auth import auth

runner = CliRunner()


def test_auth_commands():
    """Test `skaha auth` commands."""
    result = runner.invoke(auth, ["--help"])
    assert result.exit_code == 0
    results = runner.invoke(auth, ["login", "--help"])
    assert results.exit_code == 0
    result = runner.invoke(auth, ["list", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(auth, ["list"])
    assert result.exit_code == 0
    results = runner.invoke(auth, ["switch", "--help"])
    assert results.exit_code == 0
    results = runner.invoke(auth, ["use", "--help"])
    assert results.exit_code == 0
    results = runner.invoke(auth, ["use", "doesnt-exist"])
    assert results.exit_code == 1
    result = runner.invoke(auth, ["remove", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(auth, ["rm", "--help"])
    assert result.exit_code == 0
    result = runner.invoke(auth, ["rm", "doesnt-exist"])
    assert result.exit_code == 1
    results = runner.invoke(auth, ["purge", "--help"])
    assert results.exit_code == 0
    result = runner.invoke(auth, ["purge", "-y"])
    assert result.exit_code == 0
