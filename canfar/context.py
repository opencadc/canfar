"""Get available resources from the canfar server."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from canfar.client import HTTPClient

if TYPE_CHECKING:
    from httpx import Response


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

        Returns:
            A dictionary of available resources.

        Examples:
            >>> from canfar.context import Context
            >>> context = Context()
            >>> context.resources()
            {'cores': {
              'default': 1,
              'defaultRequest': 1,
              'defaultLimit': 16,
              'defaultHeadless': 1,
              'options': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
              },
             'memoryGB': {
              'default': 2,
              'defaultRequest': 4,
              'defaultLimit': 192,
              'defaultHeadless': 4,
              'options': [1,2,4...192]
             },
            'gpus': {
             'options': [1,2, ... 28]
             }
            }
        """
        response: Response = self.client.get(url="context")
        return dict(response.json())
