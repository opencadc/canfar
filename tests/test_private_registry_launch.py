"""Every private-launch credential combination, on the real Session.create path."""

from __future__ import annotations

import base64
import os
from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx2
from pydantic import SecretStr

from canfar.exceptions.session import RegistryCredentialsRequired
from canfar.models.config import Configuration
from canfar.models.registry import RegistryCredential
from canfar.sessions import Session

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

_HEADER = "X-Skaha-Registry-Auth"
_HOSTS = ("images.canfar.net", "harbor.example")
_SAVED = {
    "images.canfar.net": ("ada", "saved-ada"),
    "harbor.example": ("bob", "saved-bob"),
}
_ENV_USER = "robot"
_ENV_SECRET = "env-s3cret"
_ENV_KEYS = (
    "canfar_registry__username",
    "canfar_registry__secret",
    "canfar_registry__url",
)
_ENV_CASES = (
    ("absent", False, False, "CANFAR_REGISTRY__USERNAME", "CANFAR_REGISTRY__SECRET"),
    ("user", True, False, "CANFAR_REGISTRY__USERNAME", "CANFAR_REGISTRY__SECRET"),
    ("secret", False, True, "CANFAR_REGISTRY__USERNAME", "CANFAR_REGISTRY__SECRET"),
    ("both", True, True, "CANFAR_REGISTRY__USERNAME", "CANFAR_REGISTRY__SECRET"),
    ("both-lower", True, True, "canfar_registry__username", "canfar_registry__secret"),
)
_URLS = (None, "https://images.canfar.net/v2")
_CASES = 2 * len(_HOSTS) * (1 << len(_HOSTS)) * len(_ENV_CASES) * len(_URLS)


def _auth(username: str, secret: str) -> str:
    """Return the ``X-Skaha-Registry-Auth`` value for a username and secret."""
    return base64.b64encode(f"{username}:{secret}".encode()).decode()


def _logged_host(text: str) -> str:
    """Return the host named by the environment-fallback debug line."""
    _before, marker, rest = text.partition("No saved registry credential for ")
    if not marker:
        return ""
    host, _separator, _after = rest.partition(";")
    return host


def _saved(mask: int) -> dict[str, RegistryCredential]:
    """Return the saved credentials selected by ``mask``."""
    chosen: dict[str, RegistryCredential] = {}
    for bit, host in enumerate(_HOSTS):
        if mask & (1 << bit):
            username, secret = _SAVED[host]
            chosen[host] = RegistryCredential(
                username=username, secret=SecretStr(secret)
            )
    return chosen


def _clear_registry_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove registry environment variables in either case."""
    for key in list(os.environ):
        if key.casefold() in _ENV_KEYS:
            monkeypatch.delenv(key, raising=False)


def _respond(seen: list[httpx2.Request]):
    """Record each request and accept the launch."""

    def respond(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        name = request.url.params.get("name", "session")
        return httpx2.Response(200, text=f"{name}-id\n", request=request)

    return respond


def _check(label: str, ok: bool, detail: str) -> None:
    """Fail ``label`` with ``detail`` when ``ok`` is false."""
    if not ok:
        msg = f"{label}: {detail}"
        raise AssertionError(msg)


def _expect(
    *,
    label: str,
    private: bool,
    host: str,
    saved: dict[str, RegistryCredential],
    both: bool,
    created: object,
    posts: list[httpx2.Request],
    seen: list[httpx2.Request],
    logged: str,
    config: Configuration,
    path: Path,
) -> None:
    """Check one launch against the credential state machine."""
    if not private:
        _check(label, created == ["proto-id"], f"created {created}")
        _check(label, len(posts) == 1, f"posts {len(posts)}")
        _check(
            label,
            posts[0].headers.get(_HEADER) is None,
            "public launch sent a registry header",
        )
        _check(label, logged == "", "public launch logged a fallback")
    elif host in saved:
        username, secret = _SAVED[host]
        _check(label, created == ["proto-id"], f"created {created}")
        _check(
            label,
            posts[0].headers.get(_HEADER) == _auth(username, secret),
            "saved credential did not win",
        )
        _check(label, logged == "", "saved credential logged a fallback")
    elif both:
        _check(label, created == ["proto-id"], f"created {created}")
        _check(
            label,
            posts[0].headers.get(_HEADER) == _auth(_ENV_USER, _ENV_SECRET),
            "environment credential was not sent",
        )
        _check(label, logged == host, f"fallback log host {logged!r}")
    else:
        _check(
            label,
            isinstance(created, RegistryCredentialsRequired),
            f"created {created}",
        )
        assert isinstance(created, RegistryCredentialsRequired)
        _check(label, created.host == host, f"host {created.host}")
        _check(label, seen == [], "a request was sent")
        message = str(created)
        named = (
            "canfar registry login" in message
            and "CANFAR_REGISTRY__USERNAME" in message
            and "CANFAR_REGISTRY__SECRET" in message
        )
        _check(label, named, message)
        _check(label, logged == "", "a missing credential logged a fallback")
    _check(
        label,
        set(config.registries) == set(saved),
        f"registries became {set(config.registries)}",
    )
    for credential in config.registries.values():
        _check(
            label,
            credential.secret.get_secret_value() != _ENV_SECRET,
            "environment secret was saved",
        )
    if path.exists():
        written = path.read_text(encoding="utf-8")
        _check(label, _ENV_SECRET not in written, "environment secret was written")


def _launch(
    *,
    private: bool,
    host: str,
    saved: dict[str, RegistryCredential],
) -> tuple[object, Configuration]:
    """Run one ``Session.create`` and return its result and configuration."""
    config = Configuration(registries=dict(saved))
    session = Session(
        token=SecretStr("token"),
        url="https://example.test/skaha/v1/",
        config=config,
    )
    with session:
        try:
            return (
                session.create(
                    "proto",
                    f"{host}/proj/img:1",
                    kind="headless",
                    private=private,
                    errors="ignore",
                ),
                config,
            )
        except RegistryCredentialsRequired as err:
            return err, config


def _apply_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    user_set: bool,
    secret_set: bool,
    user_key: str,
    secret_key: str,
    url: str | None,
) -> None:
    """Install one environment combination."""
    _clear_registry_env(monkeypatch)
    if user_set:
        monkeypatch.setenv(user_key, _ENV_USER)
    if secret_set:
        monkeypatch.setenv(secret_key, _ENV_SECRET)
    if url is not None:
        monkeypatch.setenv("CANFAR_REGISTRY__URL", url)


def test_every_private_launch_decision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Saved wins, environment fills a gap, and neither sends no request."""
    path = tmp_path / "config.yaml"
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", path)
    seen: list[httpx2.Request] = []
    real_client = httpx2.Client
    checked = 0
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx2.MockTransport(_respond(seen)), **kwargs
            ),
        ),
        caplog.at_level("DEBUG", logger="canfar.models.config"),
    ):
        for private in (False, True):
            for host in _HOSTS:
                for mask in range(1 << len(_HOSTS)):
                    saved = _saved(mask)
                    for case in _ENV_CASES:
                        env_label, user_set, secret_set, user_key, secret_key = case
                        for url in _URLS:
                            checked += 1
                            _apply_env(
                                monkeypatch,
                                user_set=user_set,
                                secret_set=secret_set,
                                user_key=user_key,
                                secret_key=secret_key,
                                url=url,
                            )
                            seen.clear()
                            caplog.clear()
                            created, config = _launch(
                                private=private, host=host, saved=saved
                            )
                            posts = [
                                request for request in seen if request.method == "POST"
                            ]
                            _expect(
                                label=(
                                    f"private={private} host={host} "
                                    f"saved={sorted(saved)} env={env_label} "
                                    f"url={url!r}"
                                ),
                                private=private,
                                host=host,
                                saved=saved,
                                both=user_set and secret_set,
                                created=created,
                                posts=posts,
                                seen=seen,
                                logged=_logged_host(caplog.text),
                                config=config,
                                path=path,
                            )
    assert checked == _CASES
