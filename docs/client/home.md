# Python Client

The CANFAR Python client provides authenticated access to Sessions, Container
Images, VOSpace Services, and Science Platform metadata.

## Install and authenticate

[Install the client](get-started.md#install) first. These examples describe the unreleased
`feat/interfaces` interface; follow the installation guide to choose a
compatible environment.

```bash
canfar login cadc
```

The CLI stores the Authentication Record and Server Selection used by default
by Python clients. Python OIDC login is also available as `canfar.login()` and
`canfar.alogin()`; see [Install and set up](get-started.md).

## Core workflows

<div class="grid cards" markdown>

-   **Create Sessions**

    Launch notebooks, desktops, CARTA, Firefly, contributed apps, or headless
    workloads with `Session` or `AsyncSession`.

    [:octicons-arrow-right-16: Quickstart](quick-start.md)

-   **Read data**

    Address VOSpace Services through explicit Storage Identifiers and standard
    fsspec methods.

    [:octicons-arrow-right-16: Data access](data.md)

-   **Inspect platform state**

    Query available resources, Container Images, and Science Platform Server
    capacity.

    [:octicons-arrow-right-16: Python API reference](session.md)

</div>

<span id="minimal-example"></span>
<span id="async-example"></span>
<span id="minimal-synchronous-example"></span>
<span id="minimal-asynchronous-example"></span>

## Try the same task in Python

Both examples list your running notebooks and print the returned records.
Choose **Sync Python** for a normal script, or **Async Python** when your
application already uses `async` and `await`.

=== "Sync Python"

    ```python title="list_notebooks.py" hl_lines="1 3"
    from canfar.sessions import Session

    with Session() as session:
        notebooks = session.fetch(kind="notebook", status="Running")
        print(notebooks)
    ```

=== "Async Python"

    ```python title="list_notebooks.py" hl_lines="3 6"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            notebooks = await session.fetch(kind="notebook", status="Running")
            print(notebooks)

    if __name__ == "__main__":
        asyncio.run(main())
    ```

An empty list means no notebooks match those filters. Follow the
[Python tutorial](quick-start.md) to create, inspect, and clean up a Session.

!!! tip "Using the async example in Jupyter"

    Define `main()` without the final `if __name__` block, then run
    `await main()` in another cell. Jupyter already has an event loop.

## Main modules

| Module | Use |
| --- | --- |
| `canfar.sessions` | Create, fetch, inspect, connect, log, and destroy Sessions. |
| `canfar.images` | List Container Images or fetch parsed image details. |
| `canfar.storage` | List Storage Identifiers and build explicit fsspec filesystems. |
| `canfar.context` | Read resource limits advertised by a Science Platform Server. |
| `canfar.overview` | Check Science Platform Server availability. |
| `canfar.authentication` | Login and manage saved Authentication Records. |
| `canfar.client` | Compose lower-level synchronous or asynchronous HTTP clients. |

## Read next

- [Install and set up](get-started.md)
- [Python quickstart](quick-start.md)
- [Examples](examples.md)
- [Data access](data.md)
- [Migration guide](migration.md)
- [Use CANFAR with a coding agent](agents.md)
