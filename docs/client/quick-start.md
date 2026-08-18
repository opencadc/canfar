# Python Quickstart

This guide creates a notebook Session, checks its state, and deletes it from
Python.

## 1. Authenticate

```bash
pip install --upgrade canfar
canfar login cadc
```

Use `canfar login srcnet` for an SRCNet Identity Provider. For direct Python
OIDC login, see [login and device flow](get-started.md#authenticate).

## 2. Create a notebook

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        kind="notebook",
        image="images.canfar.net/skaha/astroml:latest",
        name="quickstart-notebook",
        cores=2,
        ram=4,
    )
    print(ids)
```

`create()` returns `list[str]`; it contains only successfully launched Session
IDs.

## 3. Inspect and connect

```python
with Session() as session:
    running = session.fetch(kind="notebook", status="Running")
    print(running)                 # list[dict[str, str]]
    session.connect([item["id"] for item in running])
```

`connect()` opens the `connectURL` for Sessions that are ready. It returns
`None`; a Session that is not running is logged and skipped.

## 4. Read events and logs

```python
with Session() as session:
    events = session.events("session-id")
    logs = session.logs("session-id")
    print(events)
    print(logs)
```

The default return values are `list[dict[str, str]]` for events and
`dict[str, str]` for logs. With `verbose=True`, both methods log their output
through `canfar.sessions` and return `None`.

## 5. Clean up

```python
with Session() as session:
    result = session.destroy("session-id")
    print(result)                 # dict[str, bool]
```

For bulk cleanup, the filters after `prefix` are keyword-only:

```python
with Session() as session:
    result = session.destroy_with(
        "quickstart-",
        kind="notebook",
        status="Completed",
    )
```

## Async version

```python
from canfar.sessions import AsyncSession


async def main() -> None:
    async with AsyncSession() as session:
        ids = await session.create(
            kind="notebook",
            image="images.canfar.net/skaha/astroml:latest",
            name="async-notebook",
        )
        if ids:
            await session.connect(ids)
            print(await session.fetch(kind="notebook", status="Running"))
            print(await session.events(ids))
            print(await session.logs(ids))
            print(await session.destroy(ids))

```

For CLI diagnostics, see [Logging](../cli/logging.md). Authentication-dependent
full integration tests are separate from the deterministic Python examples;
see [Testing](testing.md).
