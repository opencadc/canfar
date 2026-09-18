# Scale out headless work

A `headless` Session runs one command in a container and ends. `--replicas N`
launches N of them from one request. The work is done when every input is
**verified**, which is a stronger state than every Session being accepted or
finished.

## 1. Put the worker where a Session can run it

The worker script, its inputs, and its outputs live on storage the Session
mounts, or inside the image. On CADC, `arc:/projects/PROJECT/x` copied from a
laptop with `canfar data cp` is `/arc/projects/PROJECT/x` inside a Session
(see [data.md](data.md)). Give the run its own directory, such as
`/arc/projects/PROJECT/runs/RUN`, holding the worker, the manifests, the
results, and the run's records.

Use an image that holds the worker's dependencies, plus `canfar` when the
worker imports the distributed helpers, and pin a version tag. The platform's
standard images, such as `skaha/astroml`, ship the client, a release or two
behind at times. Confirm the image is listed by
`canfar image ls --kind headless`. A private image needs registry
credentials in the client configuration, shown under
[Private Container Images](https://www.opencadc.org/canfar/edge/client/get-started/#private-container-images).

## 2. Write one manifest

Record the inputs once, on persistent storage, as `[index, path]` pairs whose
`index` is unique across the whole run. Every replica reads a manifest file
instead of listing a directory, because listings can differ in order or gain
files mid-run. The run-wide `index` names each output, so any subset of the
**manifest** (a ramp sample, one part of a split run, a retry list) is itself
a valid manifest whose outputs never collide with another's.

## 3. Shard inside the worker

Each replica receives `REPLICA_ID` (1-based) and `REPLICA_COUNT`.
`canfar.helpers.distributed.chunk` gives a replica one contiguous slice, with
the remainder going to the last replica; `canfar.helpers.distributed.stripe`
gives it every Nth item, which balances a manifest sorted by input size. Both
read the two variables by default and act as a single worker when they are
absent, so the same script runs unchanged in a local test.

```python
import json
import os
from pathlib import Path

from canfar.helpers.distributed import stripe

run = Path(os.environ["RUN_DIR"])
items = json.loads(Path(os.environ["MANIFEST"]).read_text())
for index, source in stripe(items):
    target = run / "results" / f"{index:06d}.json"
    if target.exists():
        continue
    result = {"input": source}  # replace with the real reduction
    partial = target.with_name(f"partial-{target.name}")
    partial.write_text(json.dumps(result))
    partial.replace(target)
```

Write through a partial file that keeps the output's extension, then
`replace()` it, so a killed replica leaves only whole outputs; skip outputs
that exist, so a resubmission resumes the run. With fewer items than
replicas, `chunk` gives one item to each of the first replicas and nothing to
the rest. An image without `canfar` shards with
`items[int(os.environ["REPLICA_ID"]) - 1 :: int(os.environ["REPLICA_COUNT"])]`.
To size later requests, have the worker log its wall time and peak memory
(`resource.getrusage`) per item.

## 4. Ramp

Submit one replica over a ramp manifest of a few items that includes the
largest input, and verify its outputs; then two replicas over a slightly
larger one; then the full count. Stay with the Server's flexible resources
unless the ramp measured a need beyond them, and then pass `--cpu` and
`--memory` sized from that measurement. Each replica is a separate request
with its own resources, and replicas start as capacity allows rather than
together.

The Server sets `OMP_NUM_THREADS` and the matching thread variables to the
requested cores, which is 1 for a flexible request. For threaded code, pass
`--cpu N` with `--memory`, or set `--env OMP_NUM_THREADS=N` yourself.

Headless Sessions are exempt from the per-user limit on interactive Sessions,
so a large request queues as `Pending` until capacity frees up. `canfar stats`
shows the Server's requested and total cores and memory: check it first, and
tell the user when the request far exceeds what is free.

## 5. Submit and record

Every `canfar` option goes before `--`; the tokens after it are joined with
spaces into the container command, which drops shell quoting. Keep paths free
of spaces and pass inputs through the manifest.

```bash
canfar create headless IMAGE --name RUN --replicas 64 --env RUN_DIR=/arc/projects/PROJECT/runs/RUN --env MANIFEST=/arc/projects/PROJECT/runs/RUN/manifest.json -o json -- python /arc/projects/PROJECT/runs/RUN/worker.py
```

- Stdout is a JSON array of accepted Session IDs. Replicas are named `RUN-1`
  to `RUN-64`; a single replica is named `RUN`. Names take letters, digits,
  and hyphens. Repeat `--env KEY=VALUE` per variable.
- The client validates 1 to 512 replicas, 1 to 256 cores, 1 to 512 GB, and 1 to
  28 GPUs per request. `--dry-run`, used without `-o`, checks a request against
  those bounds; the Server's live options come from
  `canfar.context.Context().resources()` and can be lower.
- For more than 512 workers, split the manifest into parts and send one
  request per part, each with its own name and `MANIFEST`, into the same run
  directory. `REPLICA_COUNT` counts one request's replicas, and the run-wide
  `index` keeps the parts' outputs apart.
- Write the returned IDs to the run directory before monitoring. They are the
  run's record and its cleanup scope.
- The CLI and `AsyncSession` post replicas concurrently (`concurrency`, default
  32, at most 128); `Session.create` posts them one after another.
  `CANFAR_TIMEOUT` (seconds, default 30, at most 300) bounds each HTTP request,
  not queue time.
- Fewer IDs than replicas means partial acceptance, and an empty list means
  none was confirmed. Reconcile before resubmitting: list
  `canfar ps --all --kind headless -o json`, match this request's Session
  names, and record any Session that was accepted after its response was lost.

```python
import asyncio
import json
from pathlib import Path

from canfar.sessions import AsyncSession

RUN = Path("/arc/projects/PROJECT/runs/RUN")


async def submit(replicas: int) -> list[str]:
    async with AsyncSession(concurrency=64, timeout=120) as sessions:
        ids = await sessions.create(
            name=RUN.name,
            image="IMAGE",
            kind="headless",
            cmd="python",
            args=str(RUN / "worker.py"),
            env={"RUN_DIR": str(RUN), "MANIFEST": str(RUN / "manifest.json")},
            replicas=replicas,
        )
    (RUN / "attempt-001.json").write_text(
        json.dumps({"ids": ids, "requested": replicas})
    )
    return ids


print(asyncio.run(submit(64)))
```

## 6. Monitor with a budget

Statuses are `Pending`, `Running`, `Terminating`, and the terminal `Succeeded`,
`Completed`, `Failed`, and `Error`. One `fetch(kind="headless")` call, or one
`canfar ps --all --kind headless -o json`, returns every Session as an object
with `id`, `name`, and `status`; filter it by your recorded IDs, which costs
one request where `info(ids)` costs one per ID. Treat an ID missing from the
reply as unknown: a Server drops a finished headless Session's record after a
retention period (one hour by default), so the outputs are the evidence.

Set the deadline from the ramp: items per replica, times the measured time
per item, times three, plus an allowance for queueing. Poll once a minute.
Done when every recorded ID is terminal, missing, or past the deadline; then
save `info`, `events`, and `logs` for the IDs that are not `Succeeded` or
`Completed` beside the run. At the deadline, report the counts per status and
ask the user whether to keep waiting or cancel; the Sessions stay until they
answer. A long `Pending` is diagnosed with `canfar events SESSION_ID` and the
table in the
[batch guide](https://www.opencadc.org/canfar/edge/platform/sessions/batch/#monitor-and-troubleshoot).

## 7. Verify, then recover

Compare the outputs against the full manifest and write the pairs without a
valid output to a retry manifest. Done when every manifest item has an output
that passes its check. To recover, fix the cause, wait until the previous
requests' Sessions are terminal or deleted, then submit the retry manifest
under a new name: the worker skips finished outputs. Two requests may share a
run directory only when their manifests are disjoint.

## 8. Clean up

Delete the recorded IDs once the user asks for cleanup; `delete` takes many
IDs per call:

```bash
canfar delete SESSION_ID_1 SESSION_ID_2 --force
```

Python `destroy(ids)` returns a success boolean per ID; report any `False`.
Results, manifests, and records stay on storage.

Cleanup by name is the fallback when IDs were lost. It removes one status per
call, so repeat it for each terminal status, and pass kind and status every
time: `canfar prune` defaults to `headless` and `Succeeded`, while
`destroy_with()` defaults to `headless` and `Completed`.

```bash
canfar prune RUN headless Succeeded
canfar prune RUN headless Failed
```

A name containing regex metacharacters is matched as a regular expression, so
quote it, and a short prefix also matches the user's other runs, so use the
full request name.

The complete manifest, worker, submit, verify, and cleanup scripts are in
[Advanced examples](https://www.opencadc.org/canfar/edge/client/advanced-examples/).
Helper edge cases are in [Helpers](https://www.opencadc.org/canfar/edge/client/helpers/),
pipeline sizing in [Best practices](https://www.opencadc.org/canfar/edge/platform/best-practices/),
and lifetime, deadlines, and out-of-memory symptoms in
[Session limits](https://www.opencadc.org/canfar/edge/platform/sessions/limits/).
