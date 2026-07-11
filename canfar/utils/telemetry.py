"""Scoped OpenTelemetry adapters for safe outbound HTTP spans."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer, TracerProvider

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from opentelemetry.context import Context
    from opentelemetry.trace import Link, Span
    from opentelemetry.util.types import Attributes


def _exception_type(exception: Exception) -> str:
    module = type(exception).__module__
    name = type(exception).__qualname__
    return f"{module}.{name}" if module and module != "builtins" else name


class _SafeHTTPTracer(Tracer):
    """Delegate spans while replacing opaque exception details with their type."""

    def __init__(self, delegate: Tracer) -> None:
        self._delegate = delegate

    def start_span(
        self,
        name: str,
        context: Context | None = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
    ) -> Span:
        del record_exception, set_status_on_exception
        return self._delegate.start_span(
            name,
            context,
            kind,
            attributes,
            links,
            start_time,
            record_exception=False,
            set_status_on_exception=False,
        )

    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        context: Context | None = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
        end_on_exit: bool = True,
    ) -> Iterator[Span]:
        with self._delegate.start_as_current_span(
            name,
            context,
            kind,
            attributes,
            links,
            start_time,
            record_exception=False,
            set_status_on_exception=False,
            end_on_exit=end_on_exit,
        ) as span:
            try:
                yield span
            except Exception as exc:
                if span.is_recording():
                    if record_exception:
                        span.add_event(
                            "exception",
                            {"exception.type": _exception_type(exc)},
                        )
                    if set_status_on_exception:
                        span.set_status(Status(StatusCode.ERROR))
                raise


class _SafeHTTPTracerProvider(TracerProvider):
    """Scope safe exception recording to CANFAR's HTTPX instrumentation."""

    def __init__(self, delegate: TracerProvider) -> None:
        self._delegate = delegate

    def get_tracer(
        self,
        instrumenting_module_name: str,
        instrumenting_library_version: str | None = None,
        schema_url: str | None = None,
        attributes: Attributes = None,
    ) -> Tracer:
        return _SafeHTTPTracer(
            self._delegate.get_tracer(
                instrumenting_module_name,
                instrumenting_library_version,
                schema_url,
                attributes,
            )
        )


def safe_httpx_tracer_provider() -> TracerProvider:
    """Return a provider adapter around the configured public provider."""
    return _SafeHTTPTracerProvider(trace.get_tracer_provider())
