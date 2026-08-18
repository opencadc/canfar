# Install and Set Up

Use the CANFAR Python package to automate work on a Science Platform Server:
launch Sessions, list Container Images, fetch logs, inspect state, and clean up
resources.

## Install

```bash
pip install --upgrade canfar
```

With `uv`:

```bash
uv add canfar
```

## Authenticate

The simplest path is to authenticate with the CLI. Python then uses the saved
Authentication Record and Server Selection:

```bash
canfar login cadc
```

Use `canfar login srcnet` for an OIDC Identity Provider.

Python also exposes native synchronous and asynchronous login functions:

```python
import canfar

canfar.login("srcnet", force=True)
```

For OIDC, Python login prints only the device-flow presentation data to the
terminal, then waits for approval. The output has this shape:

```text
Verification URL: https://example.com/device
Verification URL (complete): https://example.com/device?user_code=ABC123
Device code: ABC123
```

The device code above is the user-facing code; the private OAuth device token is
never printed. The Python API does not open a browser, render a QR code, or show
CLI progress. The CLI login command owns those interactive presentation
features.

Inside an existing event loop, use `alogin()`; it performs native asynchronous
OIDC I/O and does not call `asyncio.run()`:

```python
import canfar


async def authenticate() -> None:
    await canfar.alogin("srcnet", force=True)
```

Both functions save the Authentication Record and discovered Science Platform
Servers but do not change the active Authentication or Server Selection. They
return `None`; an unknown Identity Provider raises `KeyError`, and credential or
discovery failures raise `canfar.authentication.AuthenticationError`.

## Create a Session

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        kind="notebook",
        image="images.canfar.net/skaha/astroml:latest",
        name="my-analysis",
    )
    print(ids)
```

`create()` returns `list[str]`. A failed replica is omitted and a total HTTP or
network failure returns `[]`; request validation errors still raise.

## Edit and save Configuration

`Configuration` is the persisted data shape. Its top-level fields are
`version`, `active`, `authentication`, `servers`, `registry`, and `console`.
Authentication Records are keyed by Identity Provider, Science Platform Servers
by Server Name, and `active` stores the selected references. The bound
`config.editor` is the supported editing surface:

```python
from canfar.models.config import Configuration

config = Configuration()
width = config.editor.get("console.width")
config.editor.set("console.width", 132)
config.editor.set("servers.canfar.auths", ["x509", "oidc"])
config.editor.save()
```

`get()` can return a scalar, mapping, or whole list through a dotted path. List
indices are not supported. `set()` validates before mutating the bound model;
invalid updates leave it unchanged. `save()` persists the validated
Configuration atomically. The editor itself is not part of the serialized
Configuration shape.

## Private Container Images

Pass a `ContainerRegistry` in the Configuration when creating a Session from a
private image:

```python
from canfar.models.config import Configuration
from canfar.models.registry import ContainerRegistry
from canfar.sessions import Session

config = Configuration(
    registry=ContainerRegistry(username="username", secret="CLI_SECRET")
)
with Session(config=config) as session:
    ids = session.create(
        kind="notebook",
        image="images.canfar.net/my-project/private-image:latest",
        name="private-image-test",
    )
```

## Read next

- [Python quickstart](quick-start.md)
- [Examples](examples.md)
- [Data access](data.md)
- [Authentication and Servers](../cli/authentication-contexts.md)
- [Session API](session.md)
