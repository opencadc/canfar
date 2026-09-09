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

## Minimal synchronous example

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        kind="notebook",
        image="images.canfar.net/skaha/astroml:latest",
        name="my-analysis",
    )
    if ids:
        session.connect(ids)
```

If the notebook is still starting, `connect()` skips it. Inspect the returned
IDs and retry after readiness, as shown in the [Python tutorial](quick-start.md).

## Minimal asynchronous example

```python
from canfar.sessions import AsyncSession


async def main() -> None:
    async with AsyncSession() as session:
        ids = await session.create(
            kind="headless",
            image="images.canfar.net/skaha/astroml:latest",
            name="batch-session",
            cmd="python",
            args="/arc/projects/demo/run.py",
        )
        if ids:
            await session.events(ids)
```

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
