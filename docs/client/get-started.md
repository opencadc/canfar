# Install and Set Up

Use the CANFAR Python package to automate work on a Science Platform Server:
launch Sessions, list Container Images, fetch logs, inspect state, and clean up
resources.

## Install

!!! note "Development documentation"

    The examples in this branch describe unreleased changes since v1.4.1.
    The published package does not yet contain every command and Python API
    shown here. Read [What's new](updates.md) and the [upgrade guide](migration.md)
    before changing an existing environment.

### Use the published release

Install the released package for regular use, and use the documentation that
matches that release:

```bash
pip install --upgrade canfar
```

With `uv`:

```bash
uv add canfar
```

### Try this development branch

To test the examples on `feat/interfaces`, use a separate checkout and Python
environment. With Git and `uv` installed, run:

```bash
git clone --branch feat/interfaces https://github.com/opencadc/canfar.git canfar-preview
cd canfar-preview
uv sync
source .venv/bin/activate
canfar --help
canfar ps --help
```

The activation command above is for a macOS or Linux shell. In another shell,
use `uv run canfar …` from the checkout instead. The checkout still reports
version `1.4.1`; confirm that `canfar ps --help` offers `-o/--output` and that
`canfar data --help` works before following these examples.

The Python environment is separate, but the client still uses your normal
`~/.canfar/config.yaml`. Review the [migration guide](migration.md) before
changing saved configuration.

## Authenticate

The simplest path is to authenticate with the CLI. Python then uses the saved
Authentication Record and Server Selection:

```bash
canfar login cadc
```

Use `canfar login srcnet` if your account belongs to an SRCNet identity provider
(IDP), the service that manages your login. It uses OpenID Connect (OIDC)
device authorization: follow the displayed link to approve the login.

Python also exposes native synchronous and asynchronous login functions:

```python
import canfar
from canfar import authentication, server

canfar.login("srcnet")
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
    await canfar.alogin("srcnet")
```

Both functions save the Authentication Record and discovered Science Platform
Servers but do not change the active Authentication or Server Selection. They
return `None`; an unknown Identity Provider raises `KeyError`, and credential or
discovery failures raise `canfar.authentication.AuthenticationError`.

### Select the identity and server in Python

After either Python login function completes, select the saved identity and
list its compatible servers:

```python
from canfar import authentication, server

authentication.use("srcnet")
for candidate in server.list_servers():
    print(candidate.name, candidate.url)
```

Choose a name from that output, replace `SERVER_NAME` below, and select it
before you construct a Session client:

```python
server.use("SERVER_NAME")
```

These selection functions are synchronous and save the defaults used by new
clients. In a notebook or another running event loop, run selection and
discovery in a worker thread because they can start their own event loop:

```python
import asyncio
import canfar
from canfar import authentication, server

await canfar.alogin("srcnet")
await asyncio.to_thread(authentication.use, "srcnet")
candidates = await asyncio.to_thread(server.list_servers)
for candidate in candidates:
    print(candidate.name, candidate.url)
```

After choosing a name from that output, run this in the next notebook cell:

```python
await asyncio.to_thread(server.use, "SERVER_NAME")
```

The CLI `canfar login` flow includes selection, so you can use that route instead.

Storage has its own credential requirement. The default `arc` and `vault`
services belong to CADC and use the saved CADC Authentication Record, even
when your active compute server belongs to SRCNet. Run `canfar login cadc`
to obtain those credentials, then select SRCNet again for compute with
`canfar auth use srcnet` and `canfar server use SERVER_NAME` if needed.

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

Choose an image available on your selected server using `canfar image ls
--kind notebook`; the image above is an example. Keep the returned IDs to
inspect and clean up this specific run, as shown in the [Python tutorial](quick-start.md).

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
