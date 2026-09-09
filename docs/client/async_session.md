# Asynchronous Sessions

`AsyncSession` is the native asynchronous counterpart to `Session`. It uses a
native `httpx.AsyncClient`; it is not a synchronous client wrapped in an event
loop. Use it inside an existing async application and close it with `async with`.

## Return shapes and parity

The async methods preserve the synchronous result contracts:

| Method | Result |
| --- | --- |
| `await fetch(kind=None, status=None, view=None)` | `list[dict[str, str]]` |
| `await create(...)` | `list[str]` containing the IDs that launched successfully |
| `await info(ids)` | `list[dict[str, Any]]` |
| `await logs(ids, verbose=False)` | `dict[str, str]`, or `None` when `verbose=True` |
| `await events(ids, verbose=False)` | `list[dict[str, str]]`, or `None` when `verbose=True` |
| `await destroy(ids)` / `await destroy_with(...)` | `dict[str, bool]` |
| `await connect(ids)` | `None`; opens ready Session URLs |

`create()` omits failed launches and returns `[]` when every launch fails.
Invalid request values raise before the HTTP request. Verbose logs and events
are sent to the `canfar.sessions` logger and return `None`.

`fetch(view="all")` requests the server's all-Sessions view when authorized,
and `stats()` returns aggregate Science Platform Server resource statistics.

## Async workflow

```python
from canfar.sessions import AsyncSession


async def main() -> None:
    async with AsyncSession() as session:
        ids = await session.create(
            name="async-analysis",
            image="images.canfar.net/skaha/astroml:latest",
            kind="notebook",
        )
        if ids:
            await session.connect(ids)
            print(await session.fetch(kind="notebook", status="Running"))
            print(await session.info(ids))
            print(await session.logs(ids))
            print(await session.events(ids))
            print(await session.destroy(ids))
```

For a headless Session, add `cmd`, `args`, and `env`. `cores` and `ram` request
fixed resources; omitting them uses the Science Platform Server's flexible
allocation policy.

## Select Sessions for cleanup

`destroy_with` is keyword-only after `prefix`:

```python
async with AsyncSession() as session:
    result = await session.destroy_with(
        "batch-",
        kind="headless",
        status="Completed",
    )
```

Its signature is `destroy_with(prefix, *, kind="headless", status="Completed")`.
Literal prefixes are anchored at the beginning; prefixes containing regular
expression metacharacters are treated as regular expressions.

::: canfar.sessions.AsyncSession
    handler: python
    selection:
      members:
        - fetch
        - stats
        - create
        - info
        - logs
        - events
        - destroy
        - destroy_with
        - connect
    rendering:
      members_order: source
      show_root_heading: true
      show_source: true
      heading_level: 2
