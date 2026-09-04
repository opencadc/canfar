---
name: canfar-python-client
description: >
  CANFAR Python API: Session and AsyncSession management, Context resource
  discovery, Images, Overview, Authentication/Server selection, and VOSpace
  fsspec storage. Use when automating CANFAR from Python, scientific libraries,
  CI pipelines, or building programmatic workflows.
---
# Python API

Docs: [Python client](https://www.opencadc.org/canfar/latest/client/home/)

```bash
pip install canfar --upgrade
canfar login cadc
```

## Session (synchronous)

```python
from canfar.sessions import Session

session = Session()
ids = session.create(
    name="my-analysis",
    image="images.canfar.net/skaha/astroml:latest",
    kind="notebook",
)
if not ids:
    raise RuntimeError("No Session was created")
session.connect(ids)
# ... later, after preserving scratch-only results ...
session.destroy(ids)
```

`create` returns one ID per successful launch and logs transport/HTTP failures.
For replicas, compare `len(ids)` with the requested count before assuming every
launch succeeded.

## Headless replicas

```python
ids = session.create(
    name="batch-reduce",
    image="images.canfar.net/skaha/astroml:latest",
    kind="headless",
    cmd="python",
    args="/arc/projects/mygroup/scripts/reduce.py",  # CADC example path
    cores=4,
    ram=16,
    env={"OMP_NUM_THREADS": "4"},
    replicas=8,
)
```

The current client validates 1–512 replicas. The live platform/queue can impose
lower practical limits. Each successful replica receives `REPLICA_ID` and
`REPLICA_COUNT`.

## AsyncSession

```python
from canfar.sessions import AsyncSession

async with AsyncSession() as session:
    ids = await session.create(
        name="async-job",
        image="images.canfar.net/skaha/astroml:latest",
        kind="headless",
        cmd="python",
        args="/arc/projects/demo/run.py",  # CADC example path
    )
    if ids:
        await session.events(ids, verbose=True)
```

## Discover live resources and images

Do not hard-code chart defaults or image names when the selected Server can
answer:

```python
from canfar.context import Context
from canfar.images import Images
from canfar.overview import Overview

resources = Context().resources()
notebook_images = Images().fetch(kind="notebook")
availability = Overview().availability()
```

## VOSpace through fsspec

```python
from canfar.storage import filesystem, identifiers

available = identifiers()
project = filesystem("arc")  # use an identifier returned above
project.get_file("/projects/mygroup/raw/input.fits", "/scratch/input.fits")
```

The filesystem supports standard fsspec operations and tools that already speak
fsspec. Ranged reads are backend-specific. Materialize to `/scratch` for mmap/C
extensions or when the backend cannot serve byte ranges efficiently.

## API map

| Module | Purpose |
| --- | --- |
| `canfar.sessions` | Fetch, create, inspect, logs/events, connect, destroy |
| `canfar.context` | Live resource options/defaults |
| `canfar.images` | Images allowed for Session kinds |
| `canfar.overview` | Platform availability |
| `canfar.storage` | Discovered VOSpace Services as fsspec filesystems |
| `canfar.authentication`, `canfar.server` | Authentication and Server Selection helpers |

More: [Examples](https://www.opencadc.org/canfar/latest/client/examples/) ·
[Session API](https://www.opencadc.org/canfar/latest/client/session/) ·
[Data API](https://www.opencadc.org/canfar/latest/client/data/)

## Agent rules

1. Establish Authentication and Server Selection before constructing clients.
2. Put durable multi-step data on the site's persistent project storage, not scratch.
3. Prefer headless `kind` for automation and Notebook for interactive debugging.
4. Use explicit runtime credentials in CI; never expose saved secrets in logs/artifacts.
