"""Get available resources from the canfar server."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from canfar.client import HTTPClient

if TYPE_CHECKING:
    from httpx2 import Response


class Context(HTTPClient):
    """CANFAR Context.

    This class is a subclass of the `HTTPClient` class and inherits its
    attributes and methods.

    Examples:
        >>> from canfar.context import Context
        >>> context = Context()
        >>> context.resources()
    """

    def resources(self) -> dict[str, Any]:
        """Get available resources from the canfar server.

        ``canfar.models.http.ServerResources.from_context()`` reads this payload
        into flexible and fixed limits; discovery saves them as
        ``Server.resources``.

        Returns:
            A dictionary of available resources.

        Raises:
            httpx2.HTTPStatusError: If the Server answers with an error status.

        Examples:
            >>> from canfar.context import Context
            >>> context = Context()
            >>> context.resources()
            {'cores': {
              'default': 1,
              'defaultRequest': 1,
              'defaultLimit': 16,
              'options': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
              },
             'memoryGB': {
              'default': 2,
              'defaultRequest': 4,
              'defaultLimit': 32,
              'options': [1,2,4...192]
             },
            'gpus': {
             'options': [1,2, ... 28]
             },
            'maxInteractiveSessions': 5
            }
        """
        response: Response = self.client.get(url="context")
        response.raise_for_status()
        return dict(response.json())
