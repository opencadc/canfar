"""Public HTTP observability and secret-safety contracts."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import httpx
import logfire
import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from pydantic import SecretStr

from canfar import configure_logging
from canfar.client import HTTPClient
from canfar.utils import logging as logging_utils
from canfar.utils.telemetry import _SafeHTTPTracer

if TYPE_CHECKING:
    from collections.abc import Iterator

_RESPONSE_MATERIAL_FIELD = "private-key".replace("-", "_")
_SECRETS = {
    "access": "access-token-sentinel-01",
    "refresh": "refresh-token-sentinel-02",
    "client_secret": "client-secret-sentinel-03",
    "cookie": "cookie-sentinel-04",
    "password": "password-sentinel-05",
    "certificate": "certificate-sentinel-06",
    _RESPONSE_MATERIAL_FIELD: "private-key-sentinel-07",
    "pem": "pem-sentinel-08",
}
_FAILURE_SECRETS = {
    "sync": (
        "sync-userinfo-opaque-31",
        "sync-query-opaque-32",
        "sync-header-opaque-33",
    ),
    "async": (
        "async-userinfo-opaque-34",
        "async-query-opaque-35",
        "async-header-opaque-36",
    ),
}


@pytest.fixture
def span_exporter(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[InMemorySpanExporter]:
    """Configure a real isolated exporter and restore CANFAR's callable."""
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    original_configure = logfire.configure
    previous_instrument = logging_utils._instrument_httpx  # noqa: SLF001
    configured: logfire.Logfire | None = None

    def configure_with_exporter(**kwargs: Any) -> logfire.Logfire:
        """Configure logfire while attaching this test's in-memory exporter."""
        nonlocal configured
        configured = original_configure(
            **kwargs,
            additional_span_processors=[processor],
        )
        return configured

    monkeypatch.delenv("CANFAR_OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.setattr(logfire, "configure", configure_with_exporter)
    configure_logging(loglevel="DEBUG")
    try:
        yield exporter
    finally:
        logging_utils._instrument_httpx = previous_instrument  # noqa: SLF001
        if configured is not None:
            configured.shutdown()


@pytest.mark.asyncio
async def test_explicit_logging_emits_safe_completed_http_spans(  # noqa: PLR0915
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    span_exporter: InMemorySpanExporter,
) -> None:
    """Configured sync and async clients emit the same safe completed span."""
    hostile_environment = {
        "LOGFIRE_HTTPX_CAPTURE_ALL": "true",
        "LOGFIRE_TOKEN": "ambient-logfire-token",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "https://ambient.invalid",
        "OTEL_TRACES_EXPORTER": "console",
        "OTEL_METRICS_EXPORTER": "console",
        "OTEL_LOGS_EXPORTER": "console",
        "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_CLIENT_REQUEST": ".*",
        "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_CLIENT_RESPONSE": ".*",
        "OTEL_PYTHON_HTTPX_EXCLUDED_URLS": ".*",
        "OTEL_SEMCONV_STABILITY_OPT_IN": "http",
    }
    for key, value in hostile_environment.items():
        monkeypatch.setenv(key, value)
    traceparents: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        """Assert secret-bearing request fields and return an empty payload."""
        assert request.headers["authorization"] == f"Bearer {_SECRETS['access']}"
        assert request.url.params["refresh_token"] == _SECRETS["refresh"]
        assert request.headers["cookie"] == f"session={_SECRETS['cookie']}"
        assert request.headers["x-client-secret"] == _SECRETS["client_secret"]
        request_body = request.content.decode()
        assert all(
            secret in request_body
            for secret in (
                _SECRETS["client_secret"],
                _SECRETS["password"],
                _SECRETS["certificate"],
                _SECRETS["pem"],
            )
        )
        traceparents.append(request.headers["traceparent"])
        response_body = (
            f"refresh_token={_SECRETS['refresh']} "
            f"{_RESPONSE_MATERIAL_FIELD}={_SECRETS[_RESPONSE_MATERIAL_FIELD]}"
        )
        assert _SECRETS[_RESPONSE_MATERIAL_FIELD] in response_body
        return httpx.Response(
            202,
            request=request,
            headers={
                "x-request-id": "request-123",
                "set-cookie": f"session={_SECRETS['cookie']}",
                "x-certificate": _SECRETS["certificate"],
            },
            content=response_body,
        )

    sync_transport = httpx.MockTransport(respond)
    async_transport = httpx.MockTransport(respond)
    real_client = httpx.Client
    real_async_client = httpx.AsyncClient
    url = "https://example.test/api/"
    body = (
        f"client_secret={_SECRETS['client_secret']}&"
        f"password={_SECRETS['password']}&"
        f"certificate={_SECRETS['certificate']}&"
        f"pem={_SECRETS['pem']}"
    )

    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=sync_transport,
                **kwargs,
            ),
        ),
        patch(
            "canfar.client.AsyncClient",
            side_effect=lambda **kwargs: real_async_client(
                transport=async_transport,
                **kwargs,
            ),
        ),
    ):
        client = HTTPClient(
            token=SecretStr(_SECRETS["access"]),
            url=url,
            raise_http_errors=False,
        )
        with client:
            async with client:
                assert (
                    client.client.post(
                        f"resource?refresh_token={_SECRETS['refresh']}",
                        headers={
                            "cookie": f"session={_SECRETS['cookie']}",
                            "x-client-secret": _SECRETS["client_secret"],
                        },
                        content=body,
                    ).status_code
                    == 202
                )
                assert (
                    await client.asynclient.post(
                        f"resource?refresh_token={_SECRETS['refresh']}",
                        headers={
                            "cookie": f"session={_SECRETS['cookie']}",
                            "x-client-secret": _SECRETS["client_secret"],
                        },
                        content=body,
                    )
                ).status_code == 202

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 2, [(span.name, dict(span.attributes or {})) for span in spans]
    assert len(traceparents) == 2

    for span, traceparent in zip(spans, traceparents, strict=True):
        attributes = dict(span.attributes or {})
        context = span.context
        assert context is not None
        assert (span.end_time or 0) > (span.start_time or 0)
        assert context.trace_id != 0
        assert context.span_id != 0
        assert traceparent.startswith("00-")
        assert f"{context.trace_id:032x}" in traceparent
        assert f"{context.span_id:016x}" in traceparent
        assert attributes["http.method"] == "POST"
        assert attributes["url.full"] == "https://example.test/api/resource"
        assert attributes["http.url"] == "https://example.test/api/resource"
        assert attributes["http.status_code"] == 202
        assert attributes["request_id"] == "request-123"
        assert span.events == ()
        assert not any(
            "header" in name.lower() or "body" in name.lower() for name in attributes
        )

        exported = span.to_json()
        assert all(secret not in exported for secret in _SECRETS.values())

    stderr = capsys.readouterr().err
    assert all(secret not in stderr for secret in _SECRETS.values())
    assert {key: os.environ[key] for key in hostile_environment} == (
        hostile_environment
    )


def test_preimport_propagator_env_cannot_disable_safe_http_spans() -> None:
    """Explicit logging overrides a hostile propagator cached during import."""
    environment = os.environ.copy()
    environment.pop("CANFAR_OTEL_EXPORTER_OTLP_ENDPOINT", None)
    environment["OTEL_PROPAGATORS"] = "none"
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "pytest",
            (f"{__file__}::test_explicit_logging_emits_safe_completed_http_spans"),
            "-n",
            "0",
            "-q",
            "--no-cov",
            "-p",
            "no:cacheprovider",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.asyncio
async def test_transport_failures_preserve_callers_without_exporting_secrets(
    capsys: pytest.CaptureFixture[str],
    span_exporter: InMemorySpanExporter,
) -> None:
    """Transport exceptions stay intact while completed spans are secret-free."""

    def failing_transport() -> httpx.MockTransport:
        """Build a transport that always raises a ConnectError carrying secrets."""

        def fail(request: httpx.Request) -> httpx.Response:
            """Raise a ConnectError that embeds URL and header secrets."""
            message = f"transport failed: {request.url} {request.headers['x-secret']}"
            raise httpx.ConnectError(message, request=request)

        return httpx.MockTransport(fail)

    real_client = httpx.Client
    real_async_client = httpx.AsyncClient
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=failing_transport(),
                **kwargs,
            ),
        ),
        patch(
            "canfar.client.AsyncClient",
            side_effect=lambda **kwargs: real_async_client(
                transport=failing_transport(),
                **kwargs,
            ),
        ),
    ):
        sync_userinfo, sync_query, sync_header = _FAILURE_SECRETS["sync"]
        async_userinfo, async_query, async_header = _FAILURE_SECRETS["async"]
        sync_client = HTTPClient(
            token=SecretStr("runtime-token"),
            url=f"https://user:{sync_userinfo}@example.test/api/",
            raise_http_errors=False,
        )
        async_client = HTTPClient(
            token=SecretStr("runtime-token"),
            url=f"https://user:{async_userinfo}@example.test/api/",
            raise_http_errors=False,
        )
        with sync_client:
            async with async_client:
                with pytest.raises(httpx.ConnectError) as sync_error:
                    sync_client.client.get(
                        f"resource?opaque={sync_query}",
                        headers={"x-secret": sync_header},
                    )
                with pytest.raises(httpx.ConnectError) as async_error:
                    await async_client.asynclient.get(
                        f"resource?opaque={async_query}",
                        headers={"x-secret": async_header},
                    )

    assert all(secret in str(sync_error.value) for secret in _FAILURE_SECRETS["sync"])
    assert all(secret in str(async_error.value) for secret in _FAILURE_SECRETS["async"])
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 2
    for span in spans:
        assert span.status.status_code.name == "ERROR"
        assert span.status.description is None
        assert len(span.events) == 1
        assert dict(span.events[0].attributes or {}) == {
            "exception.type": "httpx.ConnectError"
        }
    exported = "\n".join(span.to_json() for span in spans)
    stderr = capsys.readouterr().err
    for secrets in _FAILURE_SECRETS.values():
        assert all(secret not in exported for secret in secrets)
        assert all(secret not in stderr for secret in secrets)


def test_safe_tracer_honors_disabled_exception_recording() -> None:
    """The adapter preserves callers' requested exception recording policy."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = _SafeHTTPTracer(provider.get_tracer(__name__))
    error = ValueError("opaque-caller-message")

    try:
        caught: BaseException | None = None
        with tracer.start_as_current_span(
            "disabled-exception-recording",
            record_exception=False,
            set_status_on_exception=False,
        ):
            try:
                raise error
            except ValueError as exc:
                caught = exc
        assert caught is error
        span = exporter.get_finished_spans()[0]
        assert span.events == ()
        assert span.status.status_code.name == "UNSET"
    finally:
        provider.shutdown()
