# Session API

`Session` is the native synchronous Python client for user-owned Sessions on a
Science Platform Server. It inherits the HTTP and credential behavior of
`HTTPClient`.

## Return shapes and failure behavior

The current interface has these return shapes. Check the
[installation and version guidance](get-started.md) before using branch examples:

| Method | Result |
| --- | --- |
| `fetch(kind=None, status=None)` | `list[dict[str, str]]` |
| `create(...)` | `list[str]` containing the accepted Session IDs |
| `info(ids)` | `list[dict[str, Any]]` |
| `logs(ids, verbose=False)` | `dict[str, str]`, or `None` when `verbose=True` |
| `events(ids, verbose=False)` | `list[dict[str, str]]`, or `None` when `verbose=True` |
| `destroy(ids)` / `destroy_with(...)` | `dict[str, bool]` |
| `renew(ids)` | `dict[str, bool]` |
| `connect(ids)` | `None`; opens ready Session URLs |

By default, `create()` skips an individual launch after an HTTP or network
failure and logs the failure without raising. If all requested launches fail,
it returns `[]`. Validation errors in the request are raised before the HTTP
call. `info`, `logs`, `events`, `destroy`, and `renew` likewise log and leave
out failed IDs (or report `False`); see [Raise on failures](#raise-on-failures)
to raise instead.

`stats()` returns the Science Platform Server's aggregate resource statistics as a dictionary.

`logs(..., verbose=True)` and `events(..., verbose=True)` route their results to
the `canfar.sessions` logger and return `None`; configure application logging
with `canfar.configure_logging()` if the output should be visible.

<span id="creating-sessions"></span>

## Create and manage a Session

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        name="my-analysis",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
    )
    if ids:
        session.connect(ids)
        print(session.fetch(kind="notebook", status="Running"))
        print(session.info(ids))
        print(session.logs(ids))
        print(session.events(ids))
        print(session.destroy(ids))
```

When `kind="headless"`, pass `cmd`, `args`, and `env` for the command. `cores`
and `ram` request fixed resources; omitting them uses the server's flexible
allocation policy. `replicas` requests multiple Sessions and the return value
contains the successful IDs only.

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        name="batch",
        image="images.canfar.net/skaha/terminal:latest",
        kind="headless",
        cmd="python",
        args="/arc/projects/demo/run.py",
        replicas=3,
    )
```

`replicas` accepts 1 to 256; other ranges are in
[Session limits](../platform/sessions/limits.md). Request GPUs with the `gpu`
argument. The CLI option is `--gpu` as well, while the request model and the
Server's API name the field `gpus`:

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        name="training",
        image="IMAGE_WITH_GPU_LIBRARIES",
        kind="headless",
        cmd="python",
        args="/arc/projects/demo/train.py",
        cores=8,
        ram=32,
        gpu=1,
    )
```

Use an image built for the Server's GPU stack, and confirm the device inside
the Session with `nvidia-smi`.

## Select Sessions for cleanup

`destroy_with` has a keyword-only filter contract:

```python
session.destroy_with(
    "batch-",
    kind="headless",
    status="Completed",
)
```

Its signature is
`destroy_with(prefix, *, kind="headless", status="Completed", errors=None)`.
A prefix is matched literally unless it contains regular-expression
metacharacters; such a value is treated as a regular expression.

<span id="renew-an-interactive-session"></span>

## Renew an interactive Session

`renew()` (unreleased) resets the lifetime of interactive Sessions before they
expire, as the Science Portal does. It returns `True` for each renewed ID:

```python
with Session() as session:
    print(session.renew("hjko98yghj"))  # {"hjko98yghj": True}
```

<span id="raise-on-failures"></span>

## Raise on failures

Set `errors="raise"` on the client, or pass it to one call, to raise
`SessionRequestError` instead of returning partial results (unreleased).
Every request still runs first. The exception carries `results` (what the call
would have returned) and `errors`, the `httpx2.HTTPError` for each failed
Session ID, or for each 1-based replica number from `create()`.
`CANFAR_ERRORS=raise` sets the client default; a per-call `errors="ignore"`
overrides it. Authentication and validation errors raise either way.

```python
from canfar.exceptions.session import SessionRequestError

with Session(errors="raise") as session:
    try:
        session.renew(["hjko98yghj", "ikvp1jtp"])
    except SessionRequestError as err:
        print(err.results)  # {"hjko98yghj": True, "ikvp1jtp": False}
        print(err.errors)  # {"ikvp1jtp": HTTPStatusError(...)}
```

To share one connection pool across clients, see
[Share a connection pool](client.md#share-a-connection-pool).

::: canfar.sessions.Session
    handler: python
    selection:
      members:
        - fetch
        - stats
        - create
        - info
        - logs
        - events
        - renew
        - destroy
        - destroy_with
        - connect
    rendering:
      members_order: source
      show_root_heading: true
      show_source: true
      heading_level: 2
