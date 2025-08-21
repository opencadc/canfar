# Python Client Examples

These examples use the asynchronous API for best performance and scalability.

!!! note "Assumption"
      ```bash title="Authenticated via CLI"
      canfar auth login
      ```

!!! tip "Synchronous API"
    The synchronous API is also available for simple scripts and interactive use. Simply replace `AsyncSession` with `Session` and remove `async`/`await`.

## Create Sessions

### Notebook
```python title="Create a notebook session (async)"
import asyncio
from canfar.sessions import AsyncSession

async def main():
    session = AsyncSession()
    ids = await session.create(
        name="my-notebook",
        image="images.canfar.net/skaha/base-notebook:latest",
        kind="notebook",
        cores=2,
        ram=4,
    )
    print(ids)  # ["d1tsqexh"]

asyncio.run(main())
```

### Headless

- Headless sessions are are containers that execute a command and exit when complete without user interaction.
- They are useful for batch processing and distributed computing.

```python title="Replicated Headless Sessions"
import asyncio
from canfar.sessions import AsyncSession

async def main():
    session = AsyncSession()
    ids = await session.create(
        name="env-check",
        image="images.canfar.net/skaha/terminal:1.1.1",
        kind="headless",
        cmd="env",
        env={"TEST": "value"},
        replicas=3,
    )
    print(ids)  # ["mrjdtbn9", "ov6doae7", "g9b4p1p4"]

asyncio.run(main())
```

!!! example "Replica Environment Variables"
    All containers receive the following environment variables:
    - `REPLICA_COUNT` — common total number of replicas
    - `REPLICA_ID` — 1-based index of the replica (1..N)

    Use these to partition work deterministically. See [Helpers API Reference](helpers.md) for `chunk` and `stripe`.

!!! warning "Private Container Registry Access"
    Use a private Harbor image by providing registry credentials via configuration.
    ```python
    import asyncio
    from canfar.sessions import AsyncSession
    from canfar.models.registry import ContainerRegistry
    from canfar.models.config import Configuration

    async def main():
        cfg = Configuration(registry=ContainerRegistry(username="username", secret="CLI_SECRET"))
        session = AsyncSession(config=cfg)
        ids = await session.create(
            name="private-job",
            image="images.canfar.net/your/private-image:latest",
            kind="headless",
            cmd="python",
            args=["/app/run.py"],
        )
        print(ids)

    asyncio.run(main())
    ```

## Discover and Filter Sessions

```python title="Fetch & Filter Sessions"
import asyncio
from canfar.sessions import AsyncSession

async def main():
    session = AsyncSession()
    # All sessions
    all_sessions = await session.fetch()
    # Only running notebooks
    running_notebooks = await session.fetch(kind="notebook", status="Running")
    print(len(all_sessions), len(running_notebooks))

asyncio.run(main())
```

## Inspect Sessions

```python title="Session Info"
import asyncio
from canfar.sessions import AsyncSession

async def main(ids: list[str]):
    session = AsyncSession()
    info = await session.info(ids)
    print(info[0].get("connectURL"))  # notebook URL if applicable

asyncio.run(main(["d1tsqexh"]))
```

## Events and Logs

```python title="Timeline of Events"
import asyncio
from canfar.sessions import AsyncSession

async def main(ids: list[str]):
    session = AsyncSession()
    # When verbose=True, logs are printed to stdout
    await session.events(ids, verbose=True)

asyncio.run(main(["d1tsqexh"]))
```

```python title="Session Logs"
import asyncio
from canfar.sessions import AsyncSession

async def main(ids: list[str]):
    session = AsyncSession()
    await session.logs(ids, verbose=True)  # prints to stdout when verbose=True

asyncio.run(main(["d1tsqexh"]))
```

## Cluster Stats

```python title="Cluster Statistics"
import asyncio
from canfar.sessions import AsyncSession

async def main():
    session = AsyncSession()
    stats = await session.stats()
    print(stats)

asyncio.run(main())
```

## Cleanup Sessions

```python title="Destroy Sessions"
import asyncio
from canfar.sessions import AsyncSession

async def main(ids: list[str]):
    session = AsyncSession()
    result = await session.destroy(ids)
    print(result)  # {"id": True, ...}

asyncio.run(main(["mrjdtbn9", "ov6doae7"]))
```

```python title="Bulk Destroy"
import asyncio
from canfar.sessions import AsyncSession

async def main():
    session = AsyncSession()
    # Destroy sessions with names starting with "test-" that are Succeeded and headless
    result = await session.destroy_with(prefix="test-", kind="headless", status="Succeeded")
    print(result)

asyncio.run(main())
```
