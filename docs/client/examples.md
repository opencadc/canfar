# Python Client Examples

These examples use the asynchronous API for best performance and scalability.

!!! note "Assumption"
      ```bash title="Authenticated via CLI"
      canfar auth login
      ```

## Create Sessions

### Notebook

=== "Flexible Mode (Default)"

    ```python
    from canfar.sessions import Session

    session = Session()
    ids = session.create(
        name="my-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
    )
    print(ids)  # ["d1tsqexh"]
    session.connect(ids)
    ```

=== "Fixed Mode"

    ```python
    from canfar.sessions import Session

    session = Session()
    ids = session.create(
        name="my-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
        cores=2,
        ram=4,
    )
    print(ids)  # ["d1tsqexh"]
    session.connect(ids)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    session = AsyncSession()
    ids = await session.create(
        name="my-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
    )
    print(ids)  # ["d1tsqexh"]
    await session.connect(ids)
    ```

### Headless

- Headless sessions are are containers that execute a command and exit when complete without user interaction.
- They are useful for batch processing and distributed computing.


=== "Replicated Headless Sessions"

    ```python
    from canfar.sessions import Session

    session = Session()
    ids = session.create(
        name="my-headless",
        image="images.canfar.net/skaha/astroml:latest",
        kind="headless",
        cmd="echo",
        args=["Hello, World!"],
    )
    print(ids)  # ["d1tsqexh"]
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    session = AsyncSession()
    ids = await session.create(
        name="my-headless",
        image="images.canfar.net/skaha/astroml:latest",
        kind="headless",
        cmd="echo",
        args=["Hello, World!"],
    )
    print(ids)  # ["d1tsqexh"]
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

## Resource Allocation Modes

CANFAR supports two resource allocation modes for your sessions. See the [resource allocation guide](../platform/concepts.md#resource-allocation-modes) for more information.

### Examples

=== "Flexible Mode (Default)"
    ```python
    from canfar.sessions import Session

    session = Session()
    # No cores/ram specification - uses flexible allocation
    ids = session.create(
        name="flexible-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook"
    )
    ```

=== "Fixed Mode"
    ```python
    from canfar.sessions import Session

    session = Session()
    # Specify exact resources for guaranteed allocation
    ids = session.create(
        name="fixed-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
        cores=4,
        ram=8
    )
    ```

## Discover and Filter Sessions

=== "Fetch All Sessions"

    ```python
    from canfar.sessions import Session

    session = Session()
    all_sessions = session.fetch()
    print(len(all_sessions))
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    with AsyncSession() as session:
        all_sessions = await session.fetch()
        print(len(all_sessions))
    ```
<br>

=== "Fetch Running Notebooks"

    ```python
    from canfar.sessions import Session

    session = Session()
    running = session.fetch(kind="notebook", status="Running")
    print(running)
    session.connect(running)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        running = await session.fetch(kind="notebook", status="Running")
        print(running)
        await session.connect(running)
    ```
<br>

=== "Fetch Completed Headless Sessions"

    ```python
    from canfar.sessions import Session

    session = Session()
    completed = session.fetch(kind="headless", status="Succeeded")
    print(completed)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        completed = await session.fetch(kind="headless", status="Succeeded")
        print(completed)
    ```

!!! success "Kinds & Status"

    You can use any combination of the following kinds and status to filter sessions:

    - Kinds: `desktop`, `notebook`, `carta`, `headless`, `firefly`, `desktop-app`, `contributed`
    - Statuses: `Pending`, `Running`, `Terminating`, `Succeeded`, `Error`, `Failed`


## Inspect Sessions

Detailed information about the session, including resource usage, user IDs, and more.

=== "Detailed Session Information"

    ```python
    from canfar.sessions import Session

    session = Session()
    info = session.info(ids)
    print(info)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        info = await session.info(ids)
        print(info)
    ```

## Events

Events describe the steps taken by the Science Platform to launch your session

=== "Session Events"

    ```python
    from canfar.sessions import Session

    session = Session()
    events = session.events(ids, verbose=True)
    print(events)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        events = await session.events(ids, verbose=True)
        print(events)
    ```

## Logs

Logs contain the output from your session's containers. 

!!! tip "Log Retention"
    Logs are retained until your session is deleted. A completed session, i.e., `Succeeded`, `Failed`, or `Error` is kept for 24 hours before being deleted.

=== "Session Logs"

    ```python
    from canfar.sessions import Session

    session = Session()
    logs = session.logs(ids, verbose=True)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        logs = await session.logs(ids, verbose=True)
    ```

## Cleanup Sessions

!!! warning "Permanent Action"

    Deleted sessions cannot be recovered.

=== "Destroy Session(s)"

    ```python
    from canfar.sessions import Session

    session = Session()
    result = session.destroy(ids)
    print(result)  # {"id": True, ...}
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        result = await session.destroy(ids)
        print(result)  # {"id": True, ...}
    ```
<br>
=== "Bulk Destroy"

    ```python
    from canfar.sessions import Session

    session = Session()
    result = session.destroy_with(prefix="test-", kind="headless", status="Succeeded")
    print(result)  # {"id": True, ...}
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        result = await session.destroy_with(prefix="test-", kind="headless", status="Succeeded")
        print(result)  # {"id": True, ...}
    ```