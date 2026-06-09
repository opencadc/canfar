# Python Client

The CANFAR Python client wraps the Science Platform APIs for Sessions,
Container Images, Authentication-aware HTTP clients, and automation scripts.

## Install and authenticate

```bash
pip install canfar --upgrade
canfar login cadc
```

## Core workflows

<div class="grid cards" markdown>

-   **Create Sessions**

    Launch notebooks, desktops, CARTA, Firefly, contributed apps, or headless
    jobs.

    [:octicons-arrow-right-16: Quickstart](quick-start.md)

-   **Automate jobs**

    Use `Session` or `AsyncSession` to create, inspect, log, and destroy
    Sessions from Python.

    [:octicons-arrow-right-16: Examples](examples.md)

-   **Choose Servers**

    Authenticate with an IDP, select a Science Platform Server, and keep scripts
    noninteractive.

    [:octicons-arrow-right-16: Auth and Servers](../cli/authentication-contexts.md)

-   **Use references**

    Jump to generated API pages for method signatures and model details.

    [:octicons-arrow-right-16: API reference](session.md)

</div>

## Minimal example

```python
from canfar.sessions import Session

session = Session()
ids = session.create(
    kind="notebook",
    image="images.canfar.net/skaha/astroml:latest",
    name="my-analysis",
)
session.connect(ids)
```

## Async example

```python
from canfar.sessions import AsyncSession

async with AsyncSession() as session:
    ids = await session.create(
        kind="headless",
        image="images.canfar.net/skaha/astroml:latest",
        name="batch-job",
        cmd="python",
        args="/arc/projects/demo/run.py",
    )
    await session.events(ids, verbose=True)
```

## Main modules

| Module | Use |
| --- | --- |
| `canfar.sessions` | Create, fetch, inspect, connect, log, and destroy Sessions. |
| `canfar.images` | List and inspect available Container Images. |
| `canfar.authentication` | Noninteractive Authentication helpers. |
| `canfar.server` | Server discovery, validation, and selection helpers. |
| `canfar.client` | Lower-level HTTP client composition. |

## Read next

- [Install and set up](get-started.md)
- [Python quickstart](quick-start.md)
- [Examples](examples.md)
- [Migration guide](migration.md)
