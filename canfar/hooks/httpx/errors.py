"""Module for providing httpx event hooks to log error responses.

When using httpx event hooks for 'response' events, the response body is read
inside the error-handling context so that body-download errors (e.g.
ReadTimeout during streaming) are warning-logged alongside status errors.
"""

import contextlib
import re
from collections.abc import Generator

import httpx

from canfar import get_logger

log = get_logger(__name__)

CONN_ERR_MSG = (
    "Failed to establish connection within the timeout period. "
    "The server may be unreachable or not responding."
)
READ_ERR_MSG = (
    "Failed to receive response within the timeout period. "
    "The server may be overloaded or not responding."
)
WRITE_ERR_MSG = (
    "Failed to send request within the timeout period. "
    "There may be network issues or the server is not accepting requests."
)
POOL_ERR_MSG = (
    "Failed to acquire a connection from the pool within the timeout period. "
    "All connections are currently in use."
)
_BEARER_TOKEN = re.compile(
    r"(?P<prefix>\b(?:Authorization\s+)?Bearer\s+)"
    r"(?P<token>[A-Za-z0-9._~+/=-]+)",
    re.IGNORECASE,
)


def _request_url(error: httpx.RequestError) -> str:
    try:
        request = error.request
    except RuntimeError:
        return "unknown"
    return str(request.url)


def _response_text(response: httpx.Response) -> str:
    text = response.text or "No response body"
    return _BEARER_TOKEN.sub(r"\g<prefix><redacted>", text)


@contextlib.contextmanager
def _error_handling() -> Generator[None, None, None]:
    """Context manager that logs and re-raises httpx errors.

    Wraps both the body-read and ``raise_for_status()`` calls so that errors
    from either step are warning-logged.  Use as::

        with _error_handling():
            response.read()  # or await response.aread()
            response.raise_for_status()

    Raises:
        httpx.ConnectTimeout: on connect timeout.
        httpx.ReadTimeout: on read timeout.
        httpx.WriteTimeout: on write timeout.
        httpx.PoolTimeout: on pool timeout.
        httpx.HTTPStatusError: on 4xx/5xx status.
        httpx.RequestError: for other request errors.
    """
    try:
        yield
    except httpx.ConnectTimeout as err:
        log.warning(
            "%s URL: %s",
            CONN_ERR_MSG,
            _request_url(err),
            exc_info=False,
        )
        log.debug("Connect timeout details", exc_info=True)
        raise
    except httpx.ReadTimeout as err:
        log.warning(
            "%s URL: %s",
            READ_ERR_MSG,
            _request_url(err),
            exc_info=False,
        )
        log.debug("Read timeout details", exc_info=True)
        raise
    except httpx.WriteTimeout as err:
        log.warning(
            "%s URL: %s",
            WRITE_ERR_MSG,
            _request_url(err),
            exc_info=False,
        )
        log.debug("Write timeout details", exc_info=True)
        raise
    except httpx.PoolTimeout as err:
        log.warning(
            "%s URL: %s",
            POOL_ERR_MSG,
            _request_url(err),
            exc_info=False,
        )
        log.debug("Pool timeout details", exc_info=True)
        raise
    except httpx.HTTPStatusError as err:
        log.warning(
            "HTTP %d error for %s %s: %s",
            err.response.status_code,
            err.request.method,
            err.request.url,
            _response_text(err.response),
            exc_info=False,
        )
        log.debug("HTTP status error details", exc_info=True)
        raise
    except httpx.RequestError as err:
        log.warning(
            "Request error for %s: %s",
            _request_url(err),
            err,
            exc_info=False,
        )
        log.debug("Request error details", exc_info=True)
        raise


def catch(response: httpx.Response) -> None:
    """Read the response body and raise HTTPStatusError for error responses.

    Args:
        response: An httpx.Response object.

    Raises:
        httpx.ConnectTimeout: on connect timeout.
        httpx.ReadTimeout: on read timeout (body download or raise_for_status).
        httpx.WriteTimeout: on write timeout.
        httpx.PoolTimeout: on pool timeout.
        httpx.HTTPStatusError: on 4xx/5xx status.
        httpx.RequestError: for other request errors.
    """
    with _error_handling():
        response.read()
        response.raise_for_status()


async def acatch(response: httpx.Response) -> None:
    """Read the response body and raise HTTPStatusError for error responses (async).

    Args:
        response: An httpx.Response object.

    Raises:
        httpx.ConnectTimeout: on connect timeout.
        httpx.ReadTimeout: on read timeout (body download or raise_for_status).
        httpx.WriteTimeout: on write timeout.
        httpx.PoolTimeout: on pool timeout.
        httpx.HTTPStatusError: on 4xx/5xx status.
        httpx.RequestError: for other request errors.
    """
    with _error_handling():
        await response.aread()
        response.raise_for_status()
