# Python Client Examples

Follow [Install and set up](get-started.md#install) for the client version used
by these examples, then authenticate:

```bash
canfar login cadc
```

They use the public `Session` and `AsyncSession` classes directly. Both clients
preserve the same result shapes. The tabs show equivalent operations.

!!! tip "Async examples in Jupyter"

    Define `main()` without the final `if __name__` block, then run
    `await main()` in another cell. In a script, keep `asyncio.run(main())`.

<span id="async-workflow"></span>

<span id="examples"></span>

## Create Sessions

<span id="resource-allocation-modes"></span>

### Notebook

Omit `cores` and `ram` for the server's flexible allocation policy, or pass them
for a fixed resource request:

=== "Sync Python"

    ```python title="session_example.py" hl_lines="1 3"
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

=== "Async Python"

    ```python title="session_example.py" hl_lines="3 6 7"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            ids = await session.create(
                name="my-notebook",
                image="images.canfar.net/skaha/astroml:latest",
                kind="notebook",
                cores=2,
                ram=4,
            )
            print(ids)  # list[str]
            if ids:
                await session.connect(ids)

    if __name__ == "__main__":
        asyncio.run(main())
    ```

`connect()` opens only Sessions that are already Running and have an application
URL. A newly accepted Session may still be Pending, so the call can do nothing.
Use the [inspect and connect step](quick-start.md#3-inspect-and-connect) once
your Session is ready.

### Headless

Headless Sessions run a command and exit. `cmd`, `args`, and `env` are valid
for headless Sessions:

=== "Sync Python"

    ```python title="session_example.py" hl_lines="1 3"
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

=== "Async Python"

    ```python title="session_example.py" hl_lines="3 6 7"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            ids = await session.create(
                name="my-headless",
                image="images.canfar.net/skaha/terminal:latest",
                kind="headless",
                cmd="python",
                args="/arc/projects/demo/run.py",
                env={"DATASET": "example"},
                replicas=3,
            )
            print(ids)  # successful Session IDs only

    if __name__ == "__main__":
        asyncio.run(main())
    ```

If one replica fails, `create()` logs the failure and omits that ID. If all
replicas fail, it returns `[]`.

## Discover and filter Sessions

`fetch()` returns the server's list of dictionaries as
`list[dict[str, str]]`:

=== "Sync Python"

    ```python title="session_example.py" hl_lines="1 3"
    from canfar.sessions import Session

    with Session() as session:
        all_sessions = session.fetch()
        running = session.fetch(kind="notebook", status="Running")
        print(len(all_sessions), running)
    ```

=== "Async Python"

    ```python title="session_example.py" hl_lines="3 6 7"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            all_sessions = await session.fetch()
            running = await session.fetch(kind="notebook", status="Running")
            print(len(all_sessions), running)

    if __name__ == "__main__":
        asyncio.run(main())
    ```

Supported kind values are `desktop`, `notebook`, `carta`, `headless`, `firefly`,
`desktop-app`, and `contributed`. Status filters include `Pending`, `Running`,
`Terminating`, `Succeeded`, `Completed`, `Error`, and `Failed`.

<span id="inspect-sessions"></span>
<span id="events"></span>
<span id="logs"></span>

## Inspect, events, and logs

=== "Sync Python"

    ```python title="session_example.py" hl_lines="1 3"
    from canfar.sessions import Session

    with Session() as session:
        ids = ["session-id"]
        details = session.info(ids)       # list[dict[str, Any]]
        events = session.events(ids)      # list[dict[str, str]]
        logs = session.logs(ids)          # dict[str, str]
        print(details, events, logs)
    ```

=== "Async Python"

    ```python title="session_example.py" hl_lines="3 6 7"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            ids = ["session-id"]
            details = await session.info(ids)       # list[dict[str, Any]]
            events = await session.events(ids)      # list[dict[str, str]]
            logs = await session.logs(ids)          # dict[str, str]
            print(details, events, logs)

    if __name__ == "__main__":
        asyncio.run(main())
    ```

Passing `verbose=True` to `events()` or `logs()` sends the result through the
`canfar.sessions` logger and returns `None`. Configure logging with
`canfar.configure_logging()` when an application needs to display it.

<span id="cleanup-sessions"></span>

## Cleanup

!!! warning "Save results before deleting Sessions"

    The examples below make real deletion requests. Use only IDs or prefixes
    belonging to your run, after verifying its persistent outputs.

`destroy()` returns a `dict[str, bool]` keyed by requested Session ID. The
filters after `prefix` in `destroy_with()` are keyword-only:

=== "Sync Python"

    ```python title="session_example.py" hl_lines="1 3"
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

=== "Async Python"

    ```python title="session_example.py" hl_lines="3 6 7"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            print(await session.destroy("session-id"))
            print(
                await session.destroy_with(
                    "my-headless-",
                    kind="headless",
                    status="Completed",
                )
            )

    if __name__ == "__main__":
        asyncio.run(main())
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
