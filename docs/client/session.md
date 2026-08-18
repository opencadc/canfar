# Session API

`Session` is the native synchronous Python client for user-owned Sessions on a
Science Platform Server. It inherits the HTTP and credential behavior of
`HTTPClient`.

## Return shapes and failure behavior

The released Python contracts are:

| Method | Result |
| --- | --- |
| `fetch(kind=None, status=None, view=None)` | `list[dict[str, str]]` |
| `create(...)` | `list[str]` containing the IDs that launched successfully |
| `info(ids)` | `list[dict[str, Any]]` |
| `logs(ids, verbose=False)` | `dict[str, str]`, or `None` when `verbose=True` |
| `events(ids, verbose=False)` | `list[dict[str, str]]`, or `None` when `verbose=True` |
| `destroy(ids)` / `destroy_with(...)` | `dict[str, bool]` |
| `connect(ids)` | `None`; opens ready Session URLs |

`create()` skips an individual launch after an HTTP or network failure and logs
the failure without raising. If all requested launches fail, it returns `[]`.
Validation errors in the request are raised before the HTTP call.

`fetch(view="all")` requests the server's all-Sessions view when the caller is
authorized; the response remains a list of dictionaries. `stats()` returns the
Science Platform Server's aggregate resource statistics as a dictionary.

`logs(..., verbose=True)` and `events(..., verbose=True)` route their results to
the `canfar.sessions` logger and return `None`; configure application logging
with `canfar.configure_logging()` if the output should be visible.

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

## Select Sessions for cleanup

`destroy_with` has a keyword-only filter contract:

```python
session.destroy_with(
    "batch-",
    kind="headless",
    status="Completed",
)
```

Its signature is `destroy_with(prefix, *, kind="headless", status="Completed")`.
A prefix is matched literally unless it contains regular-expression
metacharacters; such a value is treated as a regular expression.

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
        - destroy
        - destroy_with
        - connect
    rendering:
      members_order: source
      show_root_heading: true
      show_source: true
      heading_level: 2
