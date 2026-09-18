# Drive CANFAR from Python

Use `Session` in synchronous scripts and `AsyncSession` inside an async
application or for many concurrent requests. Open both with `with` or
`async with`. They use the identity and Server Selection saved by CLI login;
closing a client leaves its remote Sessions running.

```python
from canfar.sessions import Session

with Session() as sessions:
    ids = sessions.create(
        name="analysis",
        image="IMAGE",
        kind="notebook",
    )
    if not ids:
        raise RuntimeError("No Session was accepted")
    print(ids, sessions.info(ids))
```

Read the signatures with `help(Session.create)` before adding arguments: the
method takes `cores`, `ram`, and `gpu`, where the CLI spells them `--cpu`,
`--memory`, and `--gpu`. `cmd`, `args` (one command-line string), and `env`
are for `kind="headless"`; [batch.md](batch.md) covers replicas.

## What the methods return

| Call | Returns |
| --- | --- |
| `create(...)` | `list[str]` of accepted IDs; failed HTTP or network attempts are left out, `[]` means none was confirmed, and an invalid request raises |
| `fetch(kind=..., status=...)` | one list of Session dictionaries from a single request |
| `info(ids)` | a list of dictionaries, one request per ID, omitting IDs whose request failed |
| `logs(ids)` | a dictionary keyed by Session ID |
| `events(ids)` | a list of `{id: text}` dictionaries |
| `destroy(ids)` | a dictionary of success booleans |
| `destroy_with(prefix, *, kind=..., status=...)` | the same, for names matching a literal prefix or a regex |
| `connect(ids)` | `None`; opens ready Sessions in a browser after one readiness check |

`logs(..., verbose=True)` and `events(..., verbose=True)` send their text to
the `canfar.sessions` logger and return `None`. A Session is ready when its
record has `status` `Running` and a nonempty `connectURL`; poll `fetch()` or
`info()` on an interval with a deadline.

## Discover what the Server offers

```python
from canfar.context import Context
from canfar.images import Images
from canfar.overview import Overview

print(Context().resources())  # live CPU, memory, and GPU options
print(Images().fetch(kind="notebook"))  # image names for one Session Kind
print(Overview().availability())  # whether the Server is up
```

## Identity in Python

`canfar.login()` and `canfar.alogin()` save credentials and discovered Servers
and leave the active identity and Server as they were. Select them with
`canfar.authentication.use` and `canfar.server.use`, or use CLI login, which
does the whole flow. Python CADC login expects an existing certificate, and
Python OIDC login prints the verification URL for the user to open.

Inside a running event loop, such as a notebook, `await canfar.alogin(...)`
and run the synchronous selection and discovery calls in a worker thread, as
in `await asyncio.to_thread(canfar.server.use, SELECTOR)`, because Server
discovery starts its own event loop.

For CI, pass `token=` or `certificate=` to the client (or set `CANFAR_TOKEN`
or `CANFAR_CERTIFICATE`). Runtime credentials override the saved record for
that client and are never persisted; supply them from the CI secret store.

Setup and selection are in
[Install and set up](https://www.opencadc.org/canfar/latest/client/get-started/),
matching sync and async operations in
[Examples](https://www.opencadc.org/canfar/latest/client/examples/), and the
full references in [Session](https://www.opencadc.org/canfar/latest/client/session/),
[AsyncSession](https://www.opencadc.org/canfar/latest/client/async_session/),
and [HTTPClient](https://www.opencadc.org/canfar/latest/client/client/).
