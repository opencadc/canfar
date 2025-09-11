"""CANFAR Image Management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from canfar import get_logger
from canfar.client import HTTPClient

if TYPE_CHECKING:
    from httpx import Response

log = get_logger(__name__)


class Images(HTTPClient):
    """CANFAR Image Management.

    This class is a subclass of the `HTTPClient` class and inherits its
    attributes and methods.

    Examples:
        >>> from canfar.images import Images
        >>> images = Images()
        >>> images.fetch()
    """

    def fetch(self, kind: str | None = None) -> list[str]:
        """Get images from CANFAR Server.

        Args:
            kind (str | None, optional): Type of image. Defaults to None.

        Returns:
            list[str]: A list of images on the server.

        Examples:
            >>> from canfar.images import Images
            >>> images = Images()
            >>> images.fetch(kind="headless")
            ['images.canfar.net/skaha/terminal:1.1.1']
        """
        data: dict[str, str] = {}
        # If kind is not None, add it to the data dictionary
        if kind:
            data["type"] = kind
        response: Response = self.client.get("image", params=data)
        payload: list[dict[str, str]] = response.json()
        return [str(image["id"]) for image in payload]
