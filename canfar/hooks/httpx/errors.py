"""Module for providing httpx event hooks to log error responses.

When using httpx event hooks, especially for 'response' events, it's crucial
to explicitly read the response body using `response.read()` (for synchronous
clients) or `await response.aread()` (for asynchronous clients) *before*
attempting to access `response.text` or calling `response.raise_for_status()`.

This is because:
1. `response.text`, `response.content`, `response.json()`, etc., are typically
   populated only after the response body has been read.
2. Event hooks are often called before httpx automatically reads the response
   body for these attributes or methods.
3. Therefore, to ensure that `response.text` (or other content attributes)
   is available for logging in the event hook, especially when an error
   occurs and `response.raise_for_status()` is called, the body must be
   read first within the hook itself. Failing to do so might result in
   empty or incomplete information being logged.
"""

import re

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


def _handle_error(response: httpx.Response) -> None:
    """Log and re-raise any error from response.raise_for_status().

    Shared error-handling core called by both ``catch`` and ``acatch`` after
    the body has already been read.  The two callers differ only in how they
    read the body (``response.read()`` vs ``await response.aread()``); every
    except branch here is identical for sync and async paths.

    Raises:
        httpx.ConnectTimeout: on connect timeout.
        httpx.ReadTimeout: on read timeout.
        httpx.WriteTimeout: on write timeout.
        httpx.PoolTimeout: on pool timeout.
        httpx.HTTPStatusError: on 4xx/5xx status.
        httpx.RequestError: for other request errors.
    """
    try:
        response.raise_for_status()
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
    """Reads the response body and raises HTTPStatusError for error responses.

    Handles various httpx exceptions with informative error messages:
    - Timeout exceptions (ConnectTimeout, ReadTimeout, WriteTimeout, PoolTimeout)
      are caught and logged with specific timeout information
    - HTTP status errors (4xx, 5xx) are logged with response details
    - Other request errors are caught and logged generally

    Args:
        response: An httpx.Response object.

    Raises:
        httpx.TimeoutException: When a timeout occurs during the request
        httpx.HTTPStatusError: When the response has an error status code
        httpx.RequestError: For other request-related errors
    """
    response.read()
    _handle_error(response)


async def acatch(response: httpx.Response) -> None:
    """Reads the response body and raises HTTPStatusError for error responses (async).

    Handles various httpx exceptions with informative error messages:
    - Timeout exceptions (ConnectTimeout, ReadTimeout, WriteTimeout, PoolTimeout)
      are caught and logged with specific timeout information
    - HTTP status errors (4xx, 5xx) are logged with response details
    - Other request errors are caught and logged generally

    Args:
        response: An httpx.Response object.

    Raises:
        httpx.TimeoutException: When a timeout occurs during the request
        httpx.HTTPStatusError: When the response has an error status code
        httpx.RequestError: For other request-related errors
    """
    await response.aread()
    _handle_error(response)
