"""Skaha Overview."""

from __future__ import annotations

from typing import TYPE_CHECKING

from defusedxml import ElementTree
from httpx import URL
from pydantic import model_validator
from typing_extensions import Self

from skaha import get_logger
from skaha.client import SkahaClient

if TYPE_CHECKING:
    from httpx import Response

log = get_logger(__name__)


class Overview(SkahaClient):
    """Overview of the Skaha Server.

    Args:
        SkahaClient (Object): Skaha Client.
    """

    @model_validator(mode="after")
    def _update_base_url(self) -> Self:
        """Update base URL for the server.

        Returns:
            Self: The current object.
        """
        url: str = str(self.client.base_url)
        base: str = url.split("/v", maxsplit=1)[0]
        # The overview endpoint is not versioned, so need to remove it
        self.client.base_url = URL(base)
        self.asynclient.base_url = URL(base)
        return self

    def availability(self) -> bool:
        """Check if the server backend is available.

        Returns:
            bool: True if the server is available, False otherwise.
        """
        response: Response = self.client.get("availability")
        data: str = response.text
        if not data:
            log.error("No data returned from availability endpoint.")
            return False
        root = ElementTree.fromstring(data)
        available = root.find(
            ".//{http://www.ivoa.net/xml/VOSIAvailability/v1.0}available",
        )
        availaibility: str | None = available.text if available is not None else None

        note = root.find(
            ".//{http://www.ivoa.net/xml/VOSIAvailability/v1.0}note",
        )
        notify: str | None = note.text if note is not None else None
        if availaibility is None:
            log.error("No availability information found in the response.")
            return False
        log.info(notify if notify else "No additional information provided.")
        return availaibility == "true"
