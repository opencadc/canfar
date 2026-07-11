# HTTPClient

The `canfar.client` module provides a comprehensive HTTP client for interacting with CANFAR Science Platform services. Built on the powerful [`httpx`](https://www.python-httpx.org/) library, it offers both synchronous and asynchronous interfaces with advanced authentication capabilities.



## Features

!!! tip "Key Capabilities"
    - **Multiple Authentication Methods**: X.509 certificates, OIDC tokens, and bearer tokens
    - **Automatic SSL Configuration**: Seamless certificate-based authentication
    - **Async/Sync Support**: Both synchronous and asynchronous HTTP clients
    - **Connection Pooling**: Optimized for concurrent requests
    - **Application Logging**: Explicit, secret-safe runtime configuration
    - **Context Managers**: Proper resource management

*This is a low-level client that is used by all other API clients in CANFAR. It is not intended to be used directly by users, but rather as a building block for other clients and contributors.*

## Authentication Modes

The client supports multiple authentication modes that can be configured through the authentication system:

## Logging

```python
from canfar import configure_logging
from canfar.client import HTTPClient

# Configure the application once, then construct clients normally.
configure_logging(loglevel="debug")
client = HTTPClient()
```

Logging is an application concern rather than an `HTTPClient` constructor
setting. See [Logging and observability](../cli/logging.md) for environment
precedence, telemetry, file output, and redaction guarantees.

## Configuration

The client composes a `Configuration` object through its `config` field:

```python
from canfar.client import HTTPClient
from canfar.models.config import Configuration

client = HTTPClient(
    config=Configuration(),
    timeout=60,           # Request timeout in seconds
    concurrency=64,       # Max concurrent connections
)
```

Runtime `token` or `certificate` arguments take precedence over saved
Authentication Records, including authentication hook selection. Without
runtime credentials, `authentication_idp` selects an Authentication Record for
that client; otherwise the active Authentication Record and Server Selection
from `Configuration` are used.

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
