# Batch processing

Use a `headless` Session when a container should run a command without a
Notebook, Desktop, CARTA, or Firefly interface. The command runs in the same
container and mounted-storage environment as an interactive Session; only the
entrypoint and lifecycle differ.

This page keeps the guidance requested in [#209](https://github.com/opencadc/canfar/issues/209):
creation output, `Pending` status, queue expectations, and checks for a job that
does not start.

## Submit a headless Session

Authenticate and put the command after `--`:

```bash
canfar login cadc
canfar create \
  --name data-reduction \
  headless skaha/astroml:latest \
  -- python /arc/projects/myproject/scripts/reduce_data.py
```

The image listing is the source of truth for names and available Session Kinds:

```bash
canfar image ls --kind headless
```

Resource options are optional. Omit them for the platform's flexible request,
or set measured requirements explicitly:

```bash
canfar create \
  --name simulation \
  --cpu 16 \
  --memory 64 \
  headless skaha/astroml:latest \
  -- python /arc/projects/myproject/scripts/simulate.py
```

Repeat `--env KEY=VALUE` for environment variables and use `--replicas` when
each container can process an independent slice:

```bash
canfar create \
  --name parameter-study \
  --replicas 10 \
  --env OMP_NUM_THREADS=4 \
  headless skaha/astroml:latest \
  -- python /arc/projects/myproject/scripts/analyse.py
```

Replicas receive `REPLICA_ID` and `REPLICA_COUNT`. Use those values or the
[distributed helpers](../../client/helpers.md) to partition work
deterministically.

## What `create` prints

The library returns the Session IDs accepted by the platform. Human CLI output
reports one successful Session as:

```text
Successfully created session 'data-reduction' (ID: SESSION_ID)
```

For multiple replicas it reports the count and lists each ID. `--output json`
or `--output yaml` emits the raw list of returned IDs as data-only output; the
same option must appear before `--`, because everything after `--` belongs to
the container command:

```bash
canfar create headless skaha/astroml:latest --output json -- python run.py
```

An empty result is a creation/transport failure, not evidence that a Session is
queued. A partial replica result returns the IDs that were accepted. Use
`--debug` for request diagnostics on stderr or increase `CANFAR_TIMEOUT` when
image pulls or platform requests need more time.

## Pending means waiting, not running

An accepted ID can remain `Pending` while the Science Platform admits the
request, waits for requested resources, pulls the image, or completes Session
initialization. `create` does not wait for `Running`, and `canfar open` only
opens a Session once it is ready.

The client does not promise a relative priority between `headless` and
interactive Sessions. Queue order and admission policy are deployment-owned;
do not assume that a headless job will outrank an interactive Session, or that
increasing a request will make it run sooner. If queue policy matters for a
project, ask the platform operator for the current policy.

## Monitor and troubleshoot

The default `ps` view shows `Pending` and `Running` Sessions. Include all
statuses when checking a new batch request:

```bash
canfar ps --all
canfar info SESSION_ID
canfar events SESSION_ID
canfar stats
```

Use `canfar logs SESSION_ID` after the container has started. A Pending Session
may have no application logs yet. Interpret the checks together:

| Observation | Next step |
| --- | --- |
| ID is absent from `ps` | Use `canfar ps --all`; confirm the create command returned an ID. |
| Status is `Pending` and events show admission/resource waiting | Reduce fixed CPU, memory, or GPU requests, or wait for capacity. |
| Status is `Pending` and events show image or initialization work | Check the image name and registry access; wait for readiness before opening it. |
| Status is `Running` but the command failed | Read `canfar logs SESSION_ID` and inspect the command, paths, and environment. |
| Status is terminal and output is missing | Check the command's exit/log output and the persistent destination; container-local paths are temporary. |
| Pending persists beyond a reasonable queue interval | Save the Session ID, `info`, `events`, `stats`, image, and resource request, then contact [support](../support/index.md). |

`canfar stats` is a Science Platform Server-level capacity signal; it does not
explain every admission decision. Events are the most useful next check for one
Session.

When a request should be cancelled, delete by ID:

```bash
canfar delete SESSION_ID
```

## Python API

`Session.create` and `AsyncSession.create` return `list[str]` Session IDs. They
do not wait for `Running`; inspect status and events separately:

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        name="nightly-reduction",
        image="images.canfar.net/skaha/astroml:latest",
        kind="headless",
        cmd="python",
        args="/arc/projects/myproject/scripts/reduce.py",
        env={"OMP_NUM_THREADS": "4"},
    )

    print(ids)
    print(session.fetch(status="Pending"))
    print(session.events(ids))
```

For native asynchronous code:

```python
import asyncio

from canfar.sessions import AsyncSession

async def main() -> None:
    async with AsyncSession() as session:
        ids = await session.create(
            name="async-batch",
            image="images.canfar.net/skaha/astroml:latest",
            kind="headless",
            cmd="python",
            args="/arc/projects/myproject/scripts/analyse.py",
            replicas=10,
        )
        print(ids)


if __name__ == "__main__":
    asyncio.run(main())
```

The `args` value is a command-line string. Keep command arguments after the
CLI's `--` delimiter so the client does not parse them as Session options.

## Storage and cleanup

Write inputs and durable outputs to `/arc/home/<user>/`,
`/arc/projects/<project>/`, or a configured VOSpace Service. Use `/scratch`
for high-speed staging and intermediates only; it is deleted when the Session
ends. See [Storage](../storage/index.md) and [Data transfers](../storage/transfers.md).

## Related guides

- [Interactive Sessions](index.md)
- [Container Images](../containers/index.md)
- [Distributed helpers](../../client/helpers.md)
- [CLI reference](../../cli/cli-help.md)
