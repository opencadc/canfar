# Advanced Examples

These patterns combine the public Session API with
`canfar.helpers.distributed`. They assume that the Session's Container Image
contains the application code and that the caller has already authenticated.

## Replicated headless processing

`replicas` creates multiple headless Sessions. Each container receives
`REPLICA_ID` (1-based) and `REPLICA_COUNT`:

```python
from canfar.sessions import AsyncSession


async def launch_batch() -> list[str]:
    async with AsyncSession() as session:
        return await session.create(
            name="fits-processing",
            image="images.canfar.net/project/analysis:latest",
            kind="headless",
            cmd="python",
            args="/app/process_observations.py",
            replicas=100,
        )
```

Pass `cores` and `ram` when every replica needs fixed resources:

```python
from canfar.sessions import AsyncSession


async def launch_fixed_batch() -> list[str]:
    async with AsyncSession() as session:
        return await session.create(
            name="fits-processing",
            image="images.canfar.net/project/analysis:latest",
            kind="headless",
            cores=8,
            ram=32,
            cmd="python",
            args="/app/process_observations.py",
            replicas=100,
        )
```

The return value contains only successfully launched Session IDs. Check for an
empty list before treating the batch as submitted.

## Partition work inside a container

Use `chunk()` for contiguous ranges and `stripe()` for round-robin assignment:

```python
from pathlib import Path

from canfar.helpers import distributed

files = list(Path("/data/observations").glob("*.fits"))

for path in distributed.chunk(files):
    print(path)

for path in distributed.stripe(files):
    print(path)
```

When `replica` and `total` are omitted, both helpers read `REPLICA_ID` and
`REPLICA_COUNT` at call time. They default to one replica when those variables
are absent. Explicit arguments override the environment:

```python
from canfar.helpers import distributed

items = list(range(10))
assert list(distributed.chunk(items, replica=1, total=4)) == [0, 1]
assert list(distributed.chunk(items, replica=4, total=4)) == [6, 7, 8, 9]
assert list(distributed.stripe(items, replica=2, total=4)) == [1, 5, 9]
```

`chunk()` raises `ValueError` for invalid replica settings. `stripe()` keeps its
legacy empty result for an out-of-range replica, but raises `ValueError` when
`total` is non-positive. See the [Helpers API](helpers.md) for the exact
contract.

## Process a VOSpace Service in each replica

Use the explicit Storage Identifier API inside a Session. The same identifier
and path remain separate Python arguments; no dynamic fsspec scheme is needed:

```python
from canfar.storage import filesystem

from canfar.helpers import distributed

paths = ["/project/observations/a.fits", "/project/observations/b.fits"]

vault = filesystem("vault")
try:
    for path in distributed.chunk(paths):
        raw = vault.cat_file(path)
        print(path, len(raw))
finally:
    vault.close()
```

For staged or memory-mapped access, use an explicit fsspec cache or
`get_file()` destination; see [Data Access](data.md).

## Cleanup a batch

Use the keyword-only filters on `destroy_with()` after the literal prefix:

```python
from canfar.sessions import Session

with Session() as session:
    result = session.destroy_with(
        "fits-processing-",
        kind="headless",
        status="Completed",
    )
    print(result)
```
