#  HTTPClient

The `canfar.client` module provides a comprehensive HTTP client for interacting with CANFAR Science Platform services. Built on the powerful [`httpx`](https://www.python-httpx.org/) library, it offers both synchronous and asynchronous interfaces with advanced authentication capabilities.



## Features

!!! tip "Key Capabilities"
    - **Multiple Authentication Methods**: X.509 certificates, OIDC tokens, and bearer tokens
    - **Automatic SSL Configuration**: Seamless certificate-based authentication
    - **Async/Sync Support**: Both synchronous and asynchronous HTTP clients
    - **Connection Pooling**: Optimized for concurrent requests
    - **Debug Logging**: Comprehensive logging for troubleshooting
    - **Context Managers**: Proper resource management

*This is a low-level client that is used by all other API clients in CANFAR. It is not intended to be used directly by users, but rather as a building block for other clients and contributors.*

## Authentication Modes

The client supports multiple authentication modes that can be configured through the authentication system:

### Debug Logging

```python
import logging
from canfar.client import HTTPClient

# Enable debug logging to see client creation details
client = HTTPClient(loglevel=logging.DEBUG)

# This will log:
# - Authentication mode selection
# - SSL context creation
# - Header generation
# - Client configuration
```

## Configuration

The client inherits from the `Configuration` class and supports all configuration options:

```python
from canfar.client import HTTPClient

client = HTTPClient(
    timeout=60,           # Request timeout in seconds
    concurrency=64,       # Max concurrent connections
    loglevel=20,         # Logging level (INFO)
)
```

## Authentication Expiry

The client provides an `expiry` property that returns the expiry time for the current authentication method:

```python
import time

client = HTTPClient()

if client.expiry:
    time_left = client.expiry - time.time()
    print(f"Authentication expires in {time_left:.0f} seconds")
else:
    print("No expiry tracking (user-provided credentials)")
```

!!! note "Expiry Tracking"
    The `expiry` property returns `None` for user-provided certificates or tokens since the client cannot track their expiry automatically.

## Error Handling

The client includes built-in error handling for HTTP responses:

```python
from httpx import HTTPStatusError

try:
    response = client.client.get("/invalid-endpoint")
    response.raise_for_status()
except HTTPStatusError as e:
    print(f"HTTP error: {e.response.status_code}")
```

## API Reference

::: canfar.client.HTTPClient
    handler: python
    options:
      members:
        - client
        - asynclient
      show_root_heading: true
      show_source: false
      heading_level: 3
      docstring_style: google
      show_signature_annotations: true
