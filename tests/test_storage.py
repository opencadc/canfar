"""Tests for private authenticated VOSpace source adapters."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, Mock

import pytest
import vosfs
from pydantic import AnyHttpUrl, AnyUrl

from canfar._storage import _vospace_source
from canfar.exceptions.context import AuthContextError
from canfar.models.active import ActiveConfig
from canfar.models.config import Configuration
from canfar.models.http import Server, VOSpaceService
from tests.helpers.config import oidc_credential, x509_credential

if TYPE_CHECKING:
    from pathlib import Path


class _Filesystem:
    """Record construction and cleanup without VOSpace I/O."""

    async_impl = True

    def __init__(self, endpoint: str, **kwargs: Any) -> None:
        self.endpoint = endpoint
        self.kwargs = kwargs
        self.asynchronous = kwargs["asynchronous"]
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


def _config(
    *,
    credential: Any,
    endpoint: str = "https://inactive.example/vospace",
) -> Configuration:
    server = Server(
        idp=credential.idp,
        uri=AnyUrl("ivo://inactive.example/skaha"),
        url=AnyHttpUrl("https://inactive.example/skaha"),
        version="v1",
        storage={
            "archive": VOSpaceService(
                uri=AnyUrl("ivo://inactive.example/arc"),
                url=AnyHttpUrl(endpoint),
            )
        },
    )
    return Configuration(
        active=ActiveConfig(authentication="active", server=None),
        authentication={
            "active": x509_credential("active"),
            credential.idp: credential,
        },
        servers={"inactive": server},
    )


@pytest.mark.asyncio
async def test_source_reloads_config_and_runtime_token_wins(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Entry reloads endpoint state and keeps token-over-certificate precedence."""
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", config_path)
    config = _config(credential=oidc_credential("inactive"))
    config.save()
    source = _vospace_source(
        "archive",
        token="runtime-token",
        certificate=tmp_path / "ignored.pem",
    )

    config.servers["inactive"].storage["archive"].url = AnyHttpUrl(
        "https://changed.example/vospace"
    )
    config.save()
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

    async with source() as filesystem:
        assert filesystem.endpoint == "https://changed.example/vospace"
        assert filesystem.kwargs == {
            "token": "runtime-token",
            "asynchronous": True,
            "skip_instance_cache": True,
        }
        assert filesystem.async_impl is True
        assert filesystem.asynchronous is True
        assert filesystem.closed is False

    assert filesystem.closed is True


@pytest.mark.asyncio
async def test_expired_inactive_oidc_refreshes_once_and_persists(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An inactive Server uses its own IDP and persists one shared refresh."""
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", config_path)
    config = _config(
        credential=oidc_credential(
            "inactive",
            access="old-access-secret",
            refresh="refresh-secret",
            access_expiry=1.0,
        )
    )
    config.save()
    refresh = AsyncMock(
        return_value={
            "access_token": "new-access-secret",
            "expires_at": 9_999_999_999.0,
        }
    )
    monkeypatch.setattr("canfar._storage.oidc.refresh", refresh)
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

    async with _vospace_source("archive")() as filesystem:
        assert filesystem.kwargs["token"] == "new-access-secret"

    refresh.assert_awaited_once_with(
        "https://oidc.example.com/token",
        "test-client",
        "test-secret",
        "refresh-secret",
    )
    persisted = Configuration()  # ty: ignore[missing-argument]
    saved = persisted.get_credential("inactive")
    assert saved.mode == "oidc"
    assert saved.token.access is not None
    assert saved.token.access.get_secret_value() == "new-access-secret"


@pytest.mark.asyncio
async def test_saved_x509_is_validated_before_construction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Saved X.509 material becomes only an inspected literal certfile path."""
    config_path = tmp_path / "config.yaml"
    certificate = tmp_path / "saved.pem"
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", config_path)
    _config(credential=x509_credential("inactive", path=certificate)).save()
    inspect = Mock()

    def inspect_certificate(path: Path) -> dict[str, object]:
        inspect(path)
        return {"path": path.as_posix(), "expiry": 9_999_999_999.0}

    monkeypatch.setattr("canfar._storage.x509.inspect", inspect_certificate)
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

    async with _vospace_source("archive")() as filesystem:
        assert filesystem.kwargs["certfile"] == certificate.as_posix()

    inspect.assert_called_once_with(certificate)


@pytest.mark.asyncio
async def test_runtime_x509_overrides_saved_oidc(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A validated runtime certificate wins over the saved Authentication Record."""
    config_path = tmp_path / "config.yaml"
    certificate = tmp_path / "runtime.pem"
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", config_path)
    _config(credential=oidc_credential("inactive")).save()
    monkeypatch.setattr(
        "canfar._storage.x509.inspect",
        lambda path: {"path": path.as_posix(), "expiry": 9_999_999_999.0},
    )
    valid = Mock(return_value=certificate.as_posix())
    monkeypatch.setattr("canfar._storage.x509.valid", valid)
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

    async with _vospace_source("archive", certificate=certificate)() as filesystem:
        assert filesystem.kwargs["certfile"] == certificate.as_posix()

    valid.assert_called_once_with(certificate)


@pytest.mark.asyncio
@pytest.mark.parametrize("exit_kind", ["error", "cancel"])
async def test_source_closes_on_failure_and_cancellation(
    exit_kind: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Context exit always closes a yielded filesystem."""
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", config_path)
    _config(credential=oidc_credential("inactive")).save()
    filesystems: list[_Filesystem] = []

    def build(endpoint: str, **kwargs: Any) -> _Filesystem:
        filesystem = _Filesystem(endpoint, **kwargs)
        filesystems.append(filesystem)
        return filesystem

    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", build)

    async def use_source() -> None:
        async with _vospace_source("archive")():
            if exit_kind == "error":
                raise RuntimeError
            await asyncio.Event().wait()

    task = asyncio.create_task(use_source())
    await asyncio.sleep(0)
    if exit_kind == "error":
        with pytest.raises(RuntimeError):
            await task
    else:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    assert filesystems[0].closed is True


@pytest.mark.asyncio
async def test_unrefreshable_oidc_fails_secret_safe_before_vospace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Bad saved auth reports a login hint without exposing secret values."""
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", config_path)
    _config(
        credential=oidc_credential(
            "inactive",
            access="old-access-secret",
            refresh="refresh-secret",
            access_expiry=1.0,
            refresh_expiry=1.0,
        )
    ).save()
    constructor = AsyncMock()
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", constructor)

    with pytest.raises(AuthContextError, match="canfar login") as exc_info:
        async with _vospace_source("archive")():
            pass

    message = str(exc_info.value)
    assert "old-access-secret" not in message
    assert "refresh-secret" not in message
    constructor.assert_not_called()
