"""CANFAR VOSpace Management."""

from __future__ import annotations

from typing import TYPE_CHECKING

import vos

from canfar import get_logger
from canfar.client import HTTPClient

if TYPE_CHECKING:
    pass

log = get_logger(__name__)


class VOSpaceClient(HTTPClient):
    """VOSpace client that inherits authentication from HTTPClient.

    This client automatically uses the active CANFAR authentication context
    to create an authenticated vos.Client instance.

    Examples:
        >>> from canfar.vospace import VOSpaceClient
        >>> vospace = VOSpaceClient()
        >>> vospace.vos_client.listdir("vos:")
    """

    def __init__(self, **kwargs):
        """Initialize VOSpaceClient with HTTPClient authentication."""
        super().__init__(**kwargs)
        self._vos_client = None

    @property
    def vos_client(self) -> vos.Client:
        """Get or create authenticated vos.Client instance.

        Returns:
            vos.Client: Authenticated VOSpace client using the active context's token.
        """
        if self._vos_client is None:
            # Extract token from active authentication context
            ctx = self.config.context

            # Get access token based on auth mode
            if hasattr(ctx, 'token') and ctx.token:
                token = ctx.token.access
            else:
                # Fallback for X509 or other auth modes
                token = None

            self._vos_client = vos.Client(vospace_token=token)

        return self._vos_client
