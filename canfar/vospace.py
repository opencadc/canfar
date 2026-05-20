"""CANFAR VOSpace Management."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import vos

from canfar import get_logger
from canfar.client import HTTPClient

if TYPE_CHECKING:
    pass

log = get_logger(__name__)

# Default VOSpace webservice host for CANFAR CLI
DEFAULT_VOSPACE_HOST = "spsrc27.iaa.csic.es"


class StorageClient(HTTPClient):
    """Storage client that inherits authentication from HTTPClient.

    This client automatically uses the active CANFAR authentication context
    to create an authenticated vos.Client instance for Cavern storage.

    The default VOSpace host is spsrc27.iaa.csic.es. This can be overridden
    by setting the VOSPACE_WEBSERVICE environment variable.

    Note:
        This client uses standard OAuth2 Bearer token authentication
        (Authorization: Bearer header) for broad compatibility with VOSpace
        services.

    Examples:
        >>> from canfar.vospace import StorageClient
        >>> storage = StorageClient()
        >>> storage.storage_client.listdir("vos:")
    """

    def __init__(self, **kwargs):
        """Initialize StorageClient with HTTPClient authentication."""
        super().__init__(**kwargs)
        self._vos_client = None
        self._token = None

    @property
    def storage_client(self) -> vos.Client:
        """Get or create authenticated vos.Client instance for Cavern storage.

        Returns:
            vos.Client: Authenticated VOSpace client using the active context's token.
        """
        if self._vos_client is None:
            # Set default VOSpace host if not already configured
            if not os.getenv("VOSPACE_WEBSERVICE") and not os.getenv("LOCAL_VOSPACE_WEBSERVICE"):
                os.environ["VOSPACE_WEBSERVICE"] = DEFAULT_VOSPACE_HOST
                log.debug(f"Using default VOSpace host: {DEFAULT_VOSPACE_HOST}")

            # Extract token from active authentication context
            ctx = self.config.context

            # Get access token based on auth mode
            if hasattr(ctx, 'token') and ctx.token:
                self._token = ctx.token.access
            else:
                # Fallback for X509 or other auth modes
                self._token = None

            # Create vos.Client WITHOUT token to avoid X-CADC-DelegationToken header
            # We'll set Bearer auth on each endpoint's session instead
            self._vos_client = vos.Client()

            # Wrap get_endpoints to add Bearer auth to sessions
            if self._token:
                self._wrap_get_endpoints()

        return self._vos_client

    def _wrap_get_endpoints(self) -> None:
        """Wrap get_endpoints to configure Bearer-only auth on endpoints.

        The vos library uses the Subject to determine available security methods
        for capability lookups. We need to:
        1. Set subject.token - so capability lookups can find authenticated URLs
        2. Set session.token - to add Authorization: Bearer header

        We do NOT use endpoint.set_auth() because it adds an X-CADC-DelegationToken
        header which some VOSpace servers (e.g., Italian) don't support.
        By setting tokens directly, we get Bearer-only auth that works across
        different VOSpace implementations.
        """
        token = self._token
        original_get_endpoints = self._vos_client.get_endpoints
        # Track which endpoints have been authenticated
        authenticated_endpoints: set = set()

        def wrapped_get_endpoints(uri):
            """Wrapper that configures Bearer-only auth on endpoints."""
            endpoint = original_get_endpoints(uri)

            if endpoint.resource_id not in authenticated_endpoints:
                try:
                    # Set token on subject for capability URL lookups
                    endpoint.conn.subject.token = token

                    # Set token on session for Bearer auth header
                    session = endpoint.conn.ws_client._get_session()
                    session.token = token

                    authenticated_endpoints.add(endpoint.resource_id)
                    log.debug(f"Configured Bearer auth for endpoint {endpoint.resource_id}")
                except AttributeError as e:
                    log.warning(f"Could not set auth for {uri}: {e}")

            return endpoint

        self._vos_client.get_endpoints = wrapped_get_endpoints
        log.debug("Configured vos.Client to use Bearer authentication")
