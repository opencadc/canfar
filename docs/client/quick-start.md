# Python Quickstart

This guide creates a notebook Session, checks its state, and deletes it from
Python.

## 1. Authenticate

[Install the client](get-started.md#install) first. These examples describe the unreleased
`feat/interfaces` interface; follow the installation guide to choose a
compatible environment.

```bash
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

`create()` returns `list[str]`; it contains only successfully created Session
IDs. If it returns `[]`, inspect the error before continuing. Creation does not
mean the application is ready. Choose an image listed by `canfar image ls
--kind notebook` on your server; the image above is an example.

## 3. Inspect and connect

```python
with Session() as session:
    details = session.info(ids)
    print(details)                 # list[dict[str, str]]
    session.connect(ids)
```

`connect()` opens the `connectURL` for Sessions that are ready. It returns
`None`; a Session that is not running is logged and skipped. If your Session
is still `Pending`, read its events below and repeat this step when it reaches
`Running`. The code uses only the IDs from your creation request.

## 4. Read events and logs

```python
with Session() as session:
    events = session.events(ids)
    logs = session.logs(ids)
    print(events)
    print(logs)
```

The default return values are `list[dict[str, str]]` for events and
`dict[str, str]` for logs. With `verbose=True`, both methods log their output
through `canfar.sessions` and return `None`.

## 5. Clean up

When you have finished the analysis, save results under `/arc` or another
persistent destination and delete the Sessions you created:

```python
with Session() as session:
    result = session.destroy(ids)
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


async def launch() -> list[str]:
    async with AsyncSession() as session:
        ids = await session.create(
            kind="notebook",
            image="images.canfar.net/skaha/astroml:latest",
            name="async-notebook",
        )
        return ids
```

In a notebook, run `ids = await launch()`. In a script, call
`ids = asyncio.run(launch())` after importing `asyncio`. Use `AsyncSession`
methods with `await` to inspect those IDs and connect after they are ready.
When your analysis is finished and saved, clean up explicitly:

```python
async def cleanup(ids: list[str]) -> None:
    async with AsyncSession() as session:
        print(await session.destroy(ids))
```

Call `await cleanup(ids)` in a notebook, or `asyncio.run(cleanup(ids))` in a
script. Closing either Python client releases its HTTP connections; it does
not delete the remote Sessions.

For CLI diagnostics, see [Logging](../cli/logging.md). Authentication-dependent
full integration tests are separate from the deterministic Python examples;
see [Testing](testing.md).
