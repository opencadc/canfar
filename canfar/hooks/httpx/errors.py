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
    try:
        response.read()
        response.raise_for_status()
    except httpx.ConnectTimeout as err:
        log.exception(
            "%s URL: %s",
            CONN_ERR_MSG,
            err.request.url,
        )
        raise
    except httpx.ReadTimeout as err:
        log.exception(
            "%s URL: %s",
            READ_ERR_MSG,
            err.request.url,
        )
        raise
    except httpx.WriteTimeout as err:
        log.exception(
            "%s URL: %s",
            WRITE_ERR_MSG,
            err.request.url,
        )
        raise
    except httpx.PoolTimeout as err:
        log.exception(
            "%s URL: %s",
            POOL_ERR_MSG,
            err.request.url,
        )
        raise
    except httpx.HTTPStatusError as err:
        log.exception(
            "HTTP %d error for %s %s: %s",
            err.response.status_code,
            err.request.method,
            err.request.url,
            err.response.text if err.response.text else "No response body",
        )
        raise
    except httpx.RequestError:
        log.exception("Request Error", stack_info=True, stacklevel=1)
        raise


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
    try:
        await response.aread()
        response.raise_for_status()
    except httpx.ConnectTimeout as err:
        log.exception(
            "%s URL: %s",
            CONN_ERR_MSG,
            err.request.url,
        )
        raise
    except httpx.ReadTimeout as err:
        log.exception(
            "%s URL: %s",
            READ_ERR_MSG,
            err.request.url,
        )
        raise
    except httpx.WriteTimeout as err:
        log.exception(
            "%s URL: %s",
            WRITE_ERR_MSG,
            err.request.url,
        )
        raise
    except httpx.PoolTimeout as err:
        log.exception(
            "%s URL: %s",
            POOL_ERR_MSG,
            err.request.url,
        )
        raise
    except httpx.HTTPStatusError as err:
        log.exception(
            "HTTP %d error for %s %s: %s",
            err.response.status_code,
            err.request.method,
            err.request.url,
            err.response.text if err.response.text else "No response body",
        )
        raise
    except httpx.RequestError:
        log.exception("Request Error", stack_info=True, stacklevel=1)
        raise
