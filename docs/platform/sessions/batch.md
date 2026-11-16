# Batch processing

Use a `headless` Session when a container should run one command without a
Notebook, Desktop, CARTA, or Firefly interface. Use a `batch` Session to run
the same command many times, as replicas of one Session. Both run in the same
container and mounted-storage environment as an interactive Session; only the
entrypoint and lifecycle differ.

Follow [Install and set up](../../client/get-started.md#install) before using
these commands. For a complete run with output verification and recovery, see
[Advanced examples](../../client/advanced-examples.md).

## Run many replicas as one batch

!!! info "Server support"
    `batch` needs a Science Platform release with batch support. On a Server
    without it, `canfar create batch` fails; headless replicas remain
    available there until the Server adds batch support.

A batch runs one command in 1 to 256 replicas, as one Session with one ID.
`--cpu`, `--memory`, and `--gpu` are the request for one replica:

```bash
canfar create batch skaha/astroml:latest \
  --name field-reduction --replicas 50 --cpu 1 --memory 4 \
  --maxfail 0.25 \
  -- python /arc/projects/myproject/scripts/worker.py
```

Each replica's container receives `CANFAR_REPLICA_INDEX`, from `0` to one less
than `--replicas`, and `CANFAR_REPLICA_COUNT`. The
[distributed helpers](../../client/helpers.md) read both, so a worker can take
its share of an ordered input list without arguments. Environment names that
start with `CANFAR_` are reserved for the platform; `--env` cannot set them.

The platform starts as many replicas as the queue has room for, at least one,
and keeps that width for the whole run. The other replicas wait until a
running replica finishes. A batch submitted while the cluster is busy can stay
narrow after capacity frees up; delete it and submit it again to use the new
room.

Each replica runs its command once, and a failed replica is not retried.
A replica can still **start again from the beginning**: a higher-priority
Session, such as an interactive one, can preempt a batch, and a node drain
replaces the replica's container. Write workers that are safe to run again:
skip inputs whose output already exists, and write each output through a
temporary file that you then rename.

`--maxfail` is a fraction from 0 to 1. The batch stops when the failed share
of its replicas reaches it:

| `--maxfail` | Replicas | Result |
| --- | --- | --- |
| unset | 50 | Every replica runs. |
| `0` | 50 | The first failed replica stops the batch. |
| `0.25` | 50 | The 13th failed replica stops the batch. |
| `1` | 50 | Every replica runs. |

Without `--maxfail`, or with `1`, the batch still ends `Failed` when any
replica failed.

Check a batch with these commands:

```bash
canfar ps --kind batch
canfar info SESSION_ID
canfar logs SESSION_ID --replica 0
canfar delete SESSION_ID
```

`ps` shows progress beside the status, for example
`Running (12/50 succeeded, 1 failed)`. `info` prints the batch document: each
replica's phase and exit code, and the CPU and memory the batch holds and
uses. A batch has one log per replica, so `logs` needs `--replica`; without
it the Server answers HTTP 400. `delete` stops every replica.

A batch ends 14 days after it starts. After it finishes, the Server keeps its
replica exit codes, logs, and batch document for 24 hours. Collect what you
need in that time; results written to `/arc` stay.

From Python, `kind="batch"` returns a list with one ID:

=== "Sync Python"

    ```python title="submit_batch.py"
    from canfar.sessions import Session

    with Session() as session:
        ids = session.create(
            name="field-reduction",
            image="images.canfar.net/skaha/astroml:latest",
            kind="batch",
            replicas=50,
            cores=1,
            ram=4,
            cmd="python",
            args="/arc/projects/myproject/scripts/worker.py",
            maxfail=0.25,
        )
        print(session.info(ids))
        print(session.logs(ids, replica=1))
    ```

=== "Async Python"

    ```python title="submit_batch.py"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            ids = await session.create(
                name="field-reduction",
                image="images.canfar.net/skaha/astroml:latest",
                kind="batch",
                replicas=50,
                cores=1,
                ram=4,
                cmd="python",
                args="/arc/projects/myproject/scripts/worker.py",
                maxfail=0.25,
            )
            print(await session.info(ids))
            print(await session.logs(ids, replica=1))

    if __name__ == "__main__":
        asyncio.run(main())
    ```

<span id="submit-from-the-cli"></span>
<span id="resource-guidance"></span>
<span id="private-images"></span>

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

Repeat `--env KEY=VALUE` for environment variables:

```bash
canfar create \
  --name parameter-study \
  --env OMP_NUM_THREADS=4 \
  headless skaha/astroml:latest \
  -- python /arc/projects/myproject/scripts/analyse.py
```

!!! warning "Headless replicas are deprecated"
    `--replicas` above 1 with `headless` creates one Session per replica,
    named `NAME-1` to `NAME-N`, each with a 1-based `REPLICA_ID` and
    `REPLICA_COUNT`. The client warns, and a later release removes it. Use a
    [batch](#run-many-replicas-as-one-batch) instead.

## What `create` prints

The library returns the Session IDs accepted by the platform. Human CLI output
reports one successful Session as:

```text
Successfully created session 'data-reduction' (ID: SESSION_ID)
```

For deprecated headless replicas it reports the count and lists each ID. A
batch reports its one ID. `--output json`
or `--output yaml` emits the raw list of returned IDs as data-only output; the
same option must appear before `--`, because everything after `--` belongs to
the container command:

```bash
canfar create headless skaha/astroml:latest --output json -- python run.py
```

An empty result is a creation/transport failure, not evidence that a Session is
queued. A partial headless replica result returns the IDs that were accepted. Use
`--debug` for request diagnostics on stderr. `CANFAR_TIMEOUT` controls HTTP
request inactivity; it does not extend queue admission or image-pull time
after a Session has been accepted.

## Pending means waiting, not running

An accepted ID can remain `Pending` while the Science Platform admits the
request, waits for requested resources, pulls the image, or completes Session
initialization. `create` does not wait for `Running`, and `canfar open` only
opens a Session once it is ready.

The client does not promise a relative priority between `headless` and
interactive Sessions. Queue order and admission policy are deployment-owned;
do not assume that a headless Session will outrank an interactive Session, or that
increasing a request will make it run sooner. If queue policy matters for a
project, ask the platform operator for the current policy.

<span id="monitor-and-clean-up"></span>
<span id="troubleshooting"></span>

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

<span id="submit-from-python"></span>

## Python API

`Session.create` and `AsyncSession.create` return `list[str]` Session IDs. They
do not wait for `Running`; inspect status and events separately:

=== "Sync Python"

    ```python title="submit_batch.py" hl_lines="1 3"
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
        if ids:
            print(session.info(ids))
            print(session.events(ids))
    ```

=== "Async Python"

    ```python title="submit_batch.py" hl_lines="3 6"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            ids = await session.create(
                name="nightly-reduction",
                image="images.canfar.net/skaha/astroml:latest",
                kind="headless",
                cmd="python",
                args="/arc/projects/myproject/scripts/reduce.py",
                env={"OMP_NUM_THREADS": "4"},
            )
            print(ids)
            if ids:
                print(await session.info(ids))
                print(await session.events(ids))

    if __name__ == "__main__":
        asyncio.run(main())
    ```

In a notebook, define `main()` without the final script entrypoint and run
`await main()` in another cell.

The `args` value is a command-line string. Keep command arguments after the
CLI's `--` delimiter so the client does not parse them as Session options.

<span id="storage-rules"></span>

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
