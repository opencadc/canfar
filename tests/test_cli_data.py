"""Tests for the embedded upstream data command group."""

from __future__ import annotations

import importlib
import sys
from contextlib import asynccontextmanager
from functools import partial
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import patch

import click
import pytest
import typer
from typer.testing import CliRunner

import canfar.cli.data as data_cli
from canfar import storage
from canfar.cli.main import cli

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Mapping
    from pathlib import Path

    from fsspec.spec import AbstractFileSystem
    from fsspec_cli import AsyncFilesystemSource

runner = CliRunner()


def _configuration(*storage_names: str) -> SimpleNamespace:
    storage = dict.fromkeys(storage_names, object())
    return SimpleNamespace(
        servers={"server": SimpleNamespace(storage=storage)},
    )


def test_root_help_advertises_data() -> None:
    """The standard CANFAR command surface contains the data group."""
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "data" in result.output


def test_upstream_app_receives_configured_sources_and_policy(monkeypatch) -> None:
    """Every app build maps all configured Servers plus local, not only active."""
    captured_sources: list[dict[str, object]] = []
    captured_capabilities: list[object] = []

    def source_factory(_name: str) -> object:
        return object()

    configurations = iter(
        [
            SimpleNamespace(
                active=SimpleNamespace(server="first"),
                servers={
                    "first": SimpleNamespace(storage={"arc": object()}),
                    "second": SimpleNamespace(storage={"cavern": object()}),
                },
            ),
            SimpleNamespace(
                active=SimpleNamespace(server="second"),
                servers={
                    "first": SimpleNamespace(storage={"arc": object()}),
                    "second": SimpleNamespace(
                        storage={"cavern": object(), "vault": object()}
                    ),
                },
            ),
        ]
    )

    def configuration() -> SimpleNamespace:
        return next(configurations)

    class FakeApp:
        def __init__(
            self,
            sources: Mapping[str, AsyncFilesystemSource],
            *,
            capabilities: object,
        ) -> None:
            captured_sources.append(dict(sources))
            captured_capabilities.append(capabilities)
            self.typer_app = typer.Typer()

    monkeypatch.setattr(storage, "Configuration", configuration)
    monkeypatch.setattr(storage, "_vospace", source_factory)
    monkeypatch.setattr(data_cli, "App", FakeApp)

    data_cli.group()
    data_cli.group()

    assert [set(sources) for sources in captured_sources] == [
        {"arc", "cavern", "local"},
        {"arc", "cavern", "vault", "local"},
    ]
    assert all(
        sources["local"] is storage._local  # noqa: SLF001
        for sources in captured_sources
    )
    assert captured_capabilities == [
        {"recursion": {"copy": True, "remove": False}},
        {"recursion": {"copy": True, "remove": False}},
    ]


@pytest.mark.asyncio
async def test_local_storage_returns_fresh_async_wrappers() -> None:
    """Each local source entry owns a fresh asynchronous wrapper."""
    async with storage._local() as first:  # noqa: SLF001
        assert first.asynchronous is True
    async with storage._local() as second:  # noqa: SLF001
        assert second.asynchronous is True

    assert first is not second
    assert first.sync_fs is not second.sync_fs


def test_data_cat_delegates_without_active_server_banner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Data stdout belongs byte-for-byte to the upstream command."""
    payload = tmp_path / "payload.txt"
    payload.write_text("upstream output\n", encoding="utf-8")
    monkeypatch.setattr(storage, "Configuration", _configuration)

    result = runner.invoke(cli, ["data", "cat", f"local:{payload}"])

    assert result.exit_code == 0, result.output
    assert result.stdout == "upstream output\n"


def test_data_long_listing_delegates_unchanged(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """The documented ``ls -lh name:/path`` form reaches upstream unchanged."""
    (tmp_path / "payload.txt").write_text("listed", encoding="utf-8")
    monkeypatch.setattr(
        storage,
        "Configuration",
        partial(_configuration, "canSRC"),
    )
    monkeypatch.setattr(
        storage,
        "_vospace",
        lambda _name: storage._local,  # noqa: SLF001
    )

    result = runner.invoke(cli, ["data", "ls", "-lh", f"canSRC:{tmp_path}"])

    assert result.exit_code == 0, result.output
    assert "payload.txt" in result.stdout


def test_data_recursive_copy_delegates_to_released_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """The embedded app retains its enabled recursive-copy behavior."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "payload.txt").write_text("copied", encoding="utf-8")
    destination = tmp_path / "destination"
    monkeypatch.setattr(
        storage,
        "Configuration",
        partial(_configuration, "canSRC"),
    )
    monkeypatch.setattr(
        storage,
        "_vospace",
        lambda _name: storage._local,  # noqa: SLF001
    )

    result = runner.invoke(
        cli,
        ["data", "cp", "-R", f"local:{source}", f"canSRC:{destination}"],
    )

    assert result.exit_code == 0, result.output
    assert (destination / "payload.txt").read_text(encoding="utf-8") == "copied"


@pytest.mark.parametrize("flag", ["-R", "-r"])
def test_data_recursive_remove_is_disabled(
    monkeypatch,
    tmp_path: Path,
    flag: str,
) -> None:
    """CANFAR keeps upstream recursive removal source-free and disabled.

    Upstream ``fsspec-cli`` v0.6.0 gave parsing to Typer, so the disabled
    ``recursion.remove`` capability now omits the flag from ``rm`` entirely
    instead of registering it and rejecting the invocation at runtime.
    """
    monkeypatch.setattr(storage, "Configuration", _configuration)

    result = runner.invoke(cli, ["data", "rm", flag, f"local:{tmp_path}"])

    assert result.exit_code == 2
    assert result.stdout == ""


def test_recursion_capability_omits_rm_flags_but_keeps_cp_flags(
    monkeypatch,
) -> None:
    """The recursion capability registers ``cp`` flags and withholds ``rm`` ones."""
    monkeypatch.setattr(storage, "Configuration", _configuration)
    group = data_cli.group()
    context = click.Context(group)

    def options(command: str) -> set[str]:
        resolved = group.get_command(context, command)
        assert resolved is not None
        return {option for param in resolved.params for option in param.opts}

    assert not options("rm") & {"-R", "-r"}
    assert {"-R", "-r"} <= options("cp")


def test_data_cross_source_move_retains_upstream_rejection(monkeypatch) -> None:
    """CANFAR does not reinterpret or implement cross-source move."""

    @asynccontextmanager
    async def unused_source() -> AsyncIterator[AbstractFileSystem]:
        msg = "source-free rejection must not acquire filesystems"
        raise AssertionError(msg)
        yield

    monkeypatch.setattr(storage, "Configuration", partial(_configuration, "arc"))
    monkeypatch.setattr(storage, "_vospace", lambda _name: unused_source)

    result = runner.invoke(cli, ["data", "mv", "arc:/a", "local:/b"])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr == "mv: cross-source move unsupported\n"


def test_importing_data_module_does_not_load_configuration() -> None:
    """Registering the command performs no configuration filesystem I/O."""
    package = sys.modules["canfar.cli"]
    original_attribute = package.data
    original = sys.modules.pop("canfar.cli.data")
    try:
        with patch(
            "canfar.models.config.Configuration",
            side_effect=AssertionError("configuration loaded during import"),
        ):
            importlib.import_module("canfar.cli.data")
    finally:
        sys.modules["canfar.cli.data"] = original
        package.data = original_attribute
