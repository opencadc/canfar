# HTTPClient

`canfar.client.HTTPClient` is the lower-level transport used by the Session,
Image, Context, and Overview clients. It composes native synchronous and
asynchronous `httpx` clients and is useful when an application needs a CANFAR
request outside those higher-level modules.

## Construct a client

```python
from canfar.client import HTTPClient
from canfar.models.config import Configuration

client = HTTPClient(
    config=Configuration(),
    timeout=60,
    concurrency=64,
)
```

The main settings are:

- `url`: an explicit Science Platform Server URL.
- `config`: the persisted `Configuration` to resolve by default.
- `authentication_idp`: a transient Identity Provider selector for this client.
- `token`: a runtime bearer token.
- `certificate`: a runtime X.509 certificate path.
- `timeout`: request timeout in seconds (1–300).
- `concurrency`: maximum async connection count (1–128).

When no explicit `url` is supplied, the active Server Selection in
`Configuration` supplies the Science Platform Server. Without a runtime
credential, `authentication_idp` selects a saved Authentication Record for this
client; otherwise the active Authentication Record is used.

## Credential precedence and lifecycle

Runtime credentials take precedence over saved Authentication Records. A
non-empty runtime `token` wins over a saved X.509 or OIDC record; a runtime
`certificate` likewise wins. An empty runtime token is treated as absent and
falls back to saved state. Runtime credentials are not persisted.

Without runtime credentials, the client resolves the selected saved record when
its sync or async HTTPX client is first created. An expired OIDC record is
refreshed through the saved Authentication Record and the refreshed token is
persisted. If the record cannot refresh or an X.509 certificate is invalid,
client construction/request setup raises the established authentication error
instead of silently sending an unauthenticated request.

Use the native context manager that matches the transport:

```python
from canfar.client import HTTPClient

with HTTPClient(token="runtime-token", url="https://example.test/skaha/v1") as client:
    response = client.client.get("context")


async def request() -> None:
    async with HTTPClient(
        token="runtime-token",
        url="https://example.test/skaha/v1",
    ) as client:
        response = await client.asynclient.get("context")
```

`client` is the native `httpx.Client`; `asynclient` is the native
`httpx.AsyncClient`. They are created lazily and closed by their matching
context manager. Do not use the async client from synchronous code or expect a
sync client to run through an event loop.

## Errors and logging

HTTP response hooks raise `httpx.HTTPStatusError` by default for unsuccessful
responses. Catch it at the application boundary when a request can fail:

```python
from httpx import HTTPStatusError

from canfar.client import HTTPClient

with HTTPClient(token="runtime-token", url="https://example.test/skaha/v1") as client:
    try:
        response = client.client.get("invalid-endpoint")
    except HTTPStatusError as exc:
        print(exc.response.status_code)
```

Authentication and configuration failures use CANFAR's authentication/error
types. Do not log tokens, certificates, or raw credential records. Configure
the application logger explicitly when diagnostics are needed:

```python
from canfar import configure_logging

configure_logging("debug")
```

## Configuration editing

`HTTPClient` consumes the persisted `Configuration`; it does not own edits or
alternate configuration services. Use `config.editor.get()`, `set()`, and
`save()` to make validated, atomic changes while preserving the stable
`version`/`active`/`authentication`/`servers`/`registry`/`console` shape. See
[Install and set up](get-started.md#edit-and-save-configuration).

## API Reference

::: canfar.client.HTTPClient
    handler: python
    options:
      members:
        - client
        - asynclient
        - uses_runtime_credentials
        - authentication_record
        - build
      show_root_heading: true
      show_source: false
      heading_level: 3
      docstring_style: google
      show_signature_annotations: true
