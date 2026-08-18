"""Tests for the VOSpace and local storage source adapters."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, Mock

import fsspec
import pytest
import vosfs
from fsspec.implementations.local import LocalFileSystem
from pydantic import AnyHttpUrl, AnyUrl

from canfar import storage
from canfar.exceptions.context import AuthContextError
from canfar.models.active import ActiveConfig
from canfar.models.config import Configuration
from canfar.models.http import Server, VOSpaceService
from canfar.storage import _sources, _vospace
from tests.helpers.config import oidc_credential, x509_credential

if TYPE_CHECKING:
    from pathlib import Path

_LISTINGS = {
    "use_listings_cache": True,
    "listings_expiry_time": 30,
    "max_paths": 1000,
}
"""Directory-listing cache settings every VOSpace filesystem is built with."""


class _Filesystem:
    """Record construction and cleanup without VOSpace I/O."""

    def __init__(self, endpoint: str, **kwargs: Any) -> None:
        self.endpoint = endpoint
        self.kwargs = kwargs
        self.asynchronous = kwargs.get("asynchronous", False)
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


@pytest.fixture(autouse=True)
def _isolate_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Isolate every source test from the developer's configuration."""
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", config_path)


@pytest.mark.asyncio
async def test_source_reloads_config_and_runtime_token_wins(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Entry reloads endpoint state and keeps token-over-certificate precedence."""
    config = _config(credential=oidc_credential("inactive"))
    config.editor.save()
    source = _vospace(
        "archive",
        token="runtime-token",
        certificate=tmp_path / "ignored.pem",
    )

    config.servers["inactive"].storage["archive"].url = AnyHttpUrl(
        "https://changed.example/vospace"
    )
    config.editor.save()
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

    async with source() as filesystem:
        assert filesystem.endpoint == "https://changed.example/vospace"
        assert filesystem.kwargs == {
            "token": "runtime-token",
            "asynchronous": True,
            "skip_instance_cache": True,
            **_LISTINGS,
        }
        assert filesystem.asynchronous is True
        assert filesystem.closed is False

    assert filesystem.closed is True


@pytest.mark.asyncio
async def test_source_factory_constructs_fresh_filesystem_per_acquisition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated acquisition constructs and closes distinct VOSpace filesystems."""
    _config(
        credential=oidc_credential("inactive", access="current-token")
    ).editor.save()
    filesystems: list[_Filesystem] = []

    def build(endpoint: str, **kwargs: Any) -> _Filesystem:
        filesystem = _Filesystem(endpoint, **kwargs)
        filesystems.append(filesystem)
        return filesystem

    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", build)
    source = _vospace("archive")

    async with source() as first:
        assert first.closed is False
    assert first.closed is True

    async with source() as second:
        assert second.closed is False
    assert second.closed is True

    assert first is not second
    assert filesystems == [first, second]


@pytest.mark.asyncio
async def test_environment_token_preserves_runtime_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The source leaves an omitted token open to HTTPClient environment settings."""
    _config(credential=x509_credential("inactive")).editor.save()
    monkeypatch.delenv("CANFAR_CERTIFICATE", raising=False)
    monkeypatch.setenv("CANFAR_TOKEN", "environment-token")
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

    async with _vospace("archive")() as filesystem:
        assert filesystem.kwargs == {
            "token": "environment-token",
            "asynchronous": True,
            "skip_instance_cache": True,
            **_LISTINGS,
        }


@pytest.mark.asyncio
async def test_environment_certificate_preserves_runtime_precedence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The source leaves an omitted certificate open to settings sources."""
    certificate = tmp_path / "environment.pem"
    _config(credential=oidc_credential("inactive")).editor.save()
    monkeypatch.delenv("CANFAR_TOKEN", raising=False)
    monkeypatch.setenv("CANFAR_CERTIFICATE", certificate.as_posix())
    monkeypatch.setattr(
        "canfar.client.x509.inspect",
        lambda path: {"path": path.as_posix(), "expiry": 9_999_999_999.0},
    )
    valid = Mock(return_value=certificate.as_posix())
    monkeypatch.setattr("canfar.client.x509.valid", valid)
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

    async with _vospace("archive")() as filesystem:
        assert filesystem.kwargs == {
            "certfile": certificate.as_posix(),
            "asynchronous": True,
            "skip_instance_cache": True,
            **_LISTINGS,
        }

    valid.assert_called_once_with(certificate)


@pytest.mark.asyncio
async def test_expired_inactive_oidc_refreshes_once_and_persists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An inactive Science Platform Server uses its IDP and persists refresh."""
    config = _config(
        credential=oidc_credential(
            "inactive",
            access="old-access-secret",
            refresh="refresh-secret",
            access_expiry=1.0,
        )
    )
    config.editor.save()
    refresh = AsyncMock(
        return_value={
            "access_token": "new-access-secret",
            "expires_at": 9_999_999_999.0,
        }
    )
    monkeypatch.setattr("canfar.client.oidc.refresh", refresh)
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

    async with _vospace("archive")() as filesystem:
        assert filesystem.kwargs["token"] == "new-access-secret"

    refresh.assert_awaited_once_with(
        "https://oidc.example.com/token",
        "test-client",
        "test-secret",
        "refresh-secret",
    )
    persisted = Configuration()  # ty: ignore[missing-argument]
    saved = persisted.authentication["inactive"]
    assert saved.mode == "oidc"
    assert saved.token.access is not None
    assert saved.token.access.get_secret_value() == "new-access-secret"


@pytest.mark.asyncio
async def test_valid_saved_oidc_access_token_is_reused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A current saved OIDC Authentication Record needs no refresh."""
    _config(
        credential=oidc_credential("inactive", access="current-token")
    ).editor.save()
    refresh = AsyncMock()
    monkeypatch.setattr("canfar.client.oidc.refresh", refresh)
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

    async with _vospace("archive")() as filesystem:
        assert filesystem.kwargs["token"] == "current-token"

    refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_saved_x509_is_validated_before_construction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Saved X.509 material becomes only an inspected literal certfile path."""
    certificate = tmp_path / "saved.pem"
    _config(credential=x509_credential("inactive", path=certificate)).editor.save()
    inspect = Mock()

    def inspect_certificate(path: Path) -> dict[str, object]:
        inspect(path)
        return {"path": path.as_posix(), "expiry": 9_999_999_999.0}

    monkeypatch.setattr("canfar.client.x509.inspect", inspect_certificate)
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

    async with _vospace("archive")() as filesystem:
        assert filesystem.kwargs["certfile"] == certificate.as_posix()

    inspect.assert_called_once_with(certificate)


@pytest.mark.asyncio
async def test_runtime_x509_overrides_saved_authentication_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A validated runtime certificate wins over the saved Authentication Record."""
    certificate = tmp_path / "runtime.pem"
    _config(credential=oidc_credential("inactive")).editor.save()
    monkeypatch.setattr(
        "canfar.client.x509.inspect",
        lambda path: {"path": path.as_posix(), "expiry": 9_999_999_999.0},
    )
    valid = Mock(return_value=certificate.as_posix())
    monkeypatch.setattr("canfar.client.x509.valid", valid)
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

    async with _vospace("archive", certificate=certificate)() as filesystem:
        assert filesystem.kwargs["certfile"] == certificate.as_posix()

    valid.assert_called_once_with(certificate)


@pytest.mark.asyncio
async def test_invalid_saved_x509_fails_before_vospace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An invalid X.509 Authentication Record fails with a clean login hint."""
    certificate = tmp_path / "invalid.pem"
    _config(credential=x509_credential("inactive", path=certificate)).editor.save()
    monkeypatch.setattr(
        "canfar.client.x509.inspect",
        Mock(side_effect=ValueError("certificate parse detail")),
    )
    constructor = Mock()
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", constructor)

    with pytest.raises(AuthContextError, match="canfar login") as exc_info:
        async with _vospace("archive")():
            pass

    assert "certificate parse detail" not in str(exc_info.value)
    constructor.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("exit_kind", ["error", "cancel"])
async def test_source_closes_on_failure_and_cancellation(
    exit_kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Context exit always closes a yielded filesystem."""
    _config(credential=oidc_credential("inactive")).editor.save()
    filesystems: list[_Filesystem] = []

    def build(endpoint: str, **kwargs: Any) -> _Filesystem:
        filesystem = _Filesystem(endpoint, **kwargs)
        filesystems.append(filesystem)
        return filesystem

    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", build)

    async def use_source() -> None:
        async with _vospace("archive")():
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
) -> None:
    """Bad saved Authentication Record reports a secret-safe login hint."""
    _config(
        credential=oidc_credential(
            "inactive",
            access="old-access-secret",
            refresh="refresh-secret",
            access_expiry=1.0,
            refresh_expiry=1.0,
        )
    ).editor.save()
    constructor = AsyncMock()
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", constructor)

    with pytest.raises(AuthContextError, match="canfar login") as exc_info:
        async with _vospace("archive")():
            pass

    message = str(exc_info.value)
    assert "old-access-secret" not in message
    assert "refresh-secret" not in message
    constructor.assert_not_called()


@pytest.mark.asyncio
async def test_empty_saved_oidc_token_fails_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty saved token cannot fall through to certificate construction."""
    _config(credential=oidc_credential("inactive", access="")).editor.save()
    constructor = Mock()
    monkeypatch.setattr(vosfs, "VOSpaceFileSystem", constructor)

    with pytest.raises(AuthContextError, match="canfar login"):
        async with _vospace("archive")():
            pass

    constructor.assert_not_called()


class TestPublicSurface:
    """Tests for the public Storage Identifier accessors."""

    def test_identifiers_lists_configured_services_and_local(self) -> None:
        """Every configured Storage Identifier is listed, with local last."""
        _config(credential=x509_credential("inactive")).editor.save()

        assert storage.identifiers() == ["archive", "local"]

    def test_identifiers_discovers_services_on_every_server(self) -> None:
        """Discovery does not narrow the list to the active Server Selection."""
        config = _config(credential=x509_credential("inactive"))
        config.servers["other"] = Server(
            idp="inactive",
            uri=AnyUrl("ivo://other.example/skaha"),
            url=AnyHttpUrl("https://other.example/skaha"),
            storage={
                "second": VOSpaceService(
                    uri=AnyUrl("ivo://other.example/second"),
                    url=AnyHttpUrl("https://other.example/second"),
                )
            },
        )
        config.editor.save()

        assert storage.identifiers() == ["archive", "second", "local"]

    def test_local_identifier_returns_a_local_filesystem(self) -> None:
        """The reserved local identifier needs no credential."""
        assert isinstance(storage.filesystem("local"), LocalFileSystem)
        assert fsspec.get_filesystem_class("file") is LocalFileSystem

    def test_filesystem_builds_a_configured_identifier(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """The explicit filesystem API resolves a configured identifier."""
        certificate = tmp_path / "saved.pem"
        _config(credential=x509_credential("inactive", path=certificate)).editor.save()
        monkeypatch.setattr(
            "canfar.client.x509.inspect",
            lambda path: {"path": path.as_posix(), "expiry": 9_999_999_999.0},
        )
        monkeypatch.setattr(vosfs, "VOSpaceFileSystem", _Filesystem)

        filesystem = storage.filesystem("archive")

        assert filesystem.endpoint == "https://inactive.example/vospace"
        assert filesystem.kwargs["certfile"] == certificate.as_posix()
        assert filesystem.kwargs["use_listings_cache"] is True

    def test_unknown_identifier_raises_key_error(self) -> None:
        """An unconfigured Storage Identifier fails explicitly."""
        _config(credential=x509_credential("inactive")).editor.save()

        with pytest.raises(KeyError, match="missing"):
            storage.filesystem("missing")

    def test_data_source_mapping_is_private(self) -> None:
        """The fsspec-cli source mapping is not a public storage API."""
        _config(credential=x509_credential("inactive")).editor.save()

        assert not hasattr(storage, "sources")
        assert set(_sources()) == {"archive", "local"}

    def test_storage_identifiers_are_not_dynamic_module_imports(self) -> None:
        """Storage Identifiers must be passed to the explicit filesystem API."""
        _config(credential=x509_credential("inactive")).editor.save()

        assert "archive" not in storage.__dict__
