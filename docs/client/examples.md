# Python Client Examples

The examples assume that an Authentication Record exists:

```bash
canfar login cadc
```

They use the public `Session` and `AsyncSession` classes directly. Both clients
preserve the same result shapes.

## Create Sessions

### Notebook

Omit `cores` and `ram` for the server's flexible allocation policy, or pass them
for a fixed resource request:

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        name="my-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
        cores=2,
        ram=4,
    )
    print(ids)  # list[str]
    if ids:
        session.connect(ids)
```

### Headless

Headless Sessions run a command and exit. `cmd`, `args`, and `env` are valid
for headless Sessions:

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        name="my-headless",
        image="images.canfar.net/skaha/terminal:latest",
        kind="headless",
        cmd="python",
        args="/arc/projects/demo/run.py",
        env={"DATASET": "example"},
        replicas=3,
    )
    print(ids)  # successful Session IDs only
```

If one replica fails, `create()` logs the failure and omits that ID. If all
replicas fail, it returns `[]`.

## Discover and filter Sessions

`fetch()` returns the server's list of dictionaries as
`list[dict[str, str]]`:

```python
from canfar.sessions import Session

with Session() as session:
    all_sessions = session.fetch()
    running = session.fetch(kind="notebook", status="Running")
    print(len(all_sessions), running)
```

Supported kind values are `desktop`, `notebook`, `carta`, `headless`, `firefly`,
`desktop-app`, and `contributed`. Status filters include `Pending`, `Running`,
`Terminating`, `Succeeded`, `Completed`, `Error`, and `Failed`.

## Inspect, events, and logs

```python
from canfar.sessions import Session

with Session() as session:
    ids = ["session-id"]
    details = session.info(ids)       # list[dict[str, Any]]
    events = session.events(ids)      # list[dict[str, str]]
    logs = session.logs(ids)          # dict[str, str]
    print(details, events, logs)
```

Passing `verbose=True` to `events()` or `logs()` sends the result through the
`canfar.sessions` logger and returns `None`. Configure logging with
`canfar.configure_logging()` when an application needs to display it.

## Async workflow

`AsyncSession` uses the native asynchronous transport. Keep the work inside an
async function and close the client with `async with`:

```python
from canfar.sessions import AsyncSession


async def main() -> None:
    async with AsyncSession() as session:
        ids = await session.create(
            name="async-headless",
            image="images.canfar.net/skaha/terminal:latest",
            kind="headless",
            cmd="python",
            args="/arc/projects/demo/run.py",
        )
        if ids:
            running = await session.fetch(kind="headless", status="Running")
            details = await session.info(ids)
            events = await session.events(ids)
            logs = await session.logs(ids)
            print(running, details, events, logs)
```

## Cleanup

`destroy()` returns a `dict[str, bool]` keyed by requested Session ID. The
filters after `prefix` in `destroy_with()` are keyword-only:

```python
from canfar.sessions import Session

with Session() as session:
    print(session.destroy("session-id"))
    print(
        session.destroy_with(
            "my-headless-",
            kind="headless",
            status="Completed",
        )
    )
```

The equivalent async call is:

```python
from canfar.sessions import AsyncSession


async def cleanup() -> None:
    async with AsyncSession() as session:
        result = await session.destroy_with(
            "my-headless-",
            kind="headless",
            status="Completed",
        )
        print(result)
```

## Private Container Registry

Use the Configuration data model when an image is private:

```python
from canfar.models.config import Configuration
from canfar.models.registry import ContainerRegistry
from canfar.sessions import Session

config = Configuration(
    registry=ContainerRegistry(username="username", secret="CLI_SECRET")
)
with Session(config=config) as session:
    ids = session.create(
        name="private-session",
        image="images.canfar.net/project/private-image:latest",
        kind="headless",
        cmd="python",
        args="/app/run.py",
    )
```
