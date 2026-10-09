# Asynchronous Sessions

`AsyncSession` is the native asynchronous counterpart to `Session`. It uses a
native `httpx2.AsyncClient`; it is not a synchronous client wrapped in an event
loop. Use it inside an existing async application and close it with `async with`.

## Return shapes and parity

The async methods preserve the synchronous result contracts:

| Method | Result |
| --- | --- |
| `await fetch(kind=None, status=None)` | `list[dict[str, str]]` |
| `await create(...)` | `list[str]` containing the IDs that launched successfully |
| `await info(ids)` | `list[dict[str, Any]]` |
| `await logs(ids, verbose=False)` | `dict[str, str]`, or `None` when `verbose=True` |
| `await events(ids, verbose=False)` | `list[dict[str, str]]`, or `None` when `verbose=True` |
| `await destroy(ids)` / `await destroy_with(...)` | `dict[str, bool]` |
| `await renew(ids)` | `dict[str, bool]` |
| `await connect(ids)` | `None`; opens ready Session URLs |

By default, `create()` omits failed launches and returns `[]` when every launch
fails; pass `errors="raise"` to raise instead (see
[Raise on failures](#raise-on-failures)). Invalid request values raise before
the HTTP request. Verbose logs and events
are sent to the `canfar.sessions` logger and return `None`.

`stats()` returns aggregate Science Platform Server resource statistics.

<span id="creating-sessions"></span>

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

Its signature is
`destroy_with(prefix, *, kind="headless", status="Completed", errors=None)`.
Literal prefixes are anchored at the beginning; prefixes containing regular
expression metacharacters are treated as regular expressions.

<span id="renew-an-interactive-session"></span>

## Renew an interactive Session

`renew()` (unreleased) resets the lifetime of interactive Sessions before they
expire. Renewals run concurrently:

```python
async with AsyncSession() as session:
    print(await session.renew(["hjko98yghj", "ikvp1jtp"]))
```

<span id="raise-on-failures"></span>

## Raise on failures

`errors="raise"` behaves as in the [synchronous client](session.md#raise-on-failures):
every request runs, then `SessionRequestError` carries `results` and the
per-ID (or per-replica) `errors`:

```python
from canfar.exceptions.session import SessionRequestError

async with AsyncSession(errors="raise") as session:
    try:
        await session.renew(["hjko98yghj", "ikvp1jtp"])
    except SessionRequestError as err:
        print(err.results, err.errors)
```

To share one `httpx2.AsyncBaseTransport` across clients, see
[Share a connection pool](client.md#share-a-connection-pool).

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
        - renew
        - destroy
        - destroy_with
        - connect
    rendering:
      members_order: source
      show_root_heading: true
      show_source: true
      heading_level: 2
