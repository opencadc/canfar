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


def catch(response: httpx.Response) -> None:
    """Reads the response body and raises HTTPStatusError for error responses.

    Args:
        response: An httpx.Response object.
    """
    response.read()
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as err:
        log.exception(err.response.text, exc_info=False, stack_info=False, stacklevel=1)  # noqa: LOG007
        raise err from err


async def acatch(response: httpx.Response) -> None:  # Renamed function
    """Reads the response body and raises HTTPStatusError for error responses (async).

    Args:
        response: An httpx.Response object.
    """
    await response.aread()
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as err:
        log.exception(err.response.text, exc_info=False, stack_info=False, stacklevel=1)  # noqa: LOG007
        raise err from err
