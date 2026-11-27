# Scale out with a batch

A `batch` Session runs one command in 1 to 256 replicas, as one Session with
one ID: `canfar create batch IMAGE --replicas N`. A `headless` Session runs
one command once. `--replicas` above 1 with `headless` still creates one
Session per replica, but it is deprecated and the client warns; use it only
on a Server where `canfar create batch` fails for lack of batch support. The
work is done when every input is **verified**, which is a stronger state than
the batch being accepted or finished.

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
behind at times; the helpers read the batch replica variables only from a
release with batch support. Confirm the image is listed by
`canfar image ls --kind headless`. A private image uses its full
`HOST/PROJECT/IMAGE:TAG` name and `--private` (or `private=True` in Python).
A private launch needs a saved credential or
`CANFAR_REGISTRY__USERNAME` and `CANFAR_REGISTRY__SECRET`. Public images need
none. Details are under
[Private Container Images](https://www.opencadc.org/canfar/edge/client/get-started/#private-container-images).

## 2. Write one manifest

Record the inputs once, on persistent storage, as `[index, path]` pairs whose
`index` is unique across the whole run. Every replica reads a manifest file
instead of listing a directory, because listings can differ in order or gain
files mid-run. The run-wide `index` names each output, so any subset of the
**manifest** (a ramp sample, one part of a split run, a retry list) is itself
a valid manifest whose outputs never collide with another's.

## 3. Shard inside the worker

Each batch replica receives `CANFAR_REPLICA_INDEX` (0-based) and
`CANFAR_REPLICA_COUNT`; a deprecated headless replica receives `REPLICA_ID`
(1-based) and `REPLICA_COUNT`. `canfar.helpers.distributed.chunk` gives a
replica one contiguous slice, with the remainder going to the last replica;
`canfar.helpers.distributed.stripe` gives it every Nth item, which balances a
manifest sorted by input size. Both read either pair by default and act as a
single worker when neither is set, so the same script runs unchanged in a
local test.

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

Workers must be safe to run again. A batch replica runs its command once, but
it can start again from the beginning after a higher-priority Session
preempts the batch or a node drains. Write through a partial file that keeps
the output's extension, then `replace()` it, so a killed replica leaves only
whole outputs; skip outputs that exist, so a restarted replica or a
resubmission repeats no finished work. With fewer items than replicas, `chunk`
gives one item to each of the first replicas and nothing to the rest. An
image without `canfar` shards with
`items[int(os.environ["CANFAR_REPLICA_INDEX"]) :: int(os.environ["CANFAR_REPLICA_COUNT"])]`.
To size later requests, have the worker log its wall time and peak memory
(`resource.getrusage`) per item.

## 4. Ramp

Submit one replica over a ramp manifest of a few items that includes the
largest input, and verify its outputs; then two replicas over a slightly
larger one; then the full count. Stay with the Server's flexible resources
unless the ramp measured a need beyond them, and then pass `--cpu` and
`--memory` sized from that measurement; they are the request for one replica.

The platform starts as many replicas as the queue has room for, at least one,
and keeps that width for the whole run; the rest wait for a running replica
to finish. A batch submitted while the cluster is busy can stay narrow after
capacity frees up. When `canfar ps` shows few active replicas and
`canfar stats` shows free capacity, delete the batch and submit it again: the
worker skips finished outputs.

The Server sets `OMP_NUM_THREADS` and the matching thread variables to the
requested cores, which is low, typically 1, for a flexible request. For
threaded code, pass `--cpu N` with `--memory`, or set
`--env OMP_NUM_THREADS=N` yourself.

Batch and headless Sessions are exempt from the per-user limit on interactive
Sessions, so a large request queues as `Pending` until capacity frees up.
`canfar stats` shows the Server's requested and total cores and memory: check
it first, and tell the user when the request far exceeds what is free.

## 5. Submit and record

Every `canfar` option goes before `--`; the tokens after it are joined with
spaces into the container command, which drops shell quoting. Keep paths free
of spaces and pass inputs through the manifest.

```bash
canfar create batch IMAGE --name RUN --replicas 64 --maxfail 0.1 --env RUN_DIR=/arc/projects/PROJECT/runs/RUN --env MANIFEST=/arc/projects/PROJECT/runs/RUN/manifest.json -o json -- python /arc/projects/PROJECT/runs/RUN/worker.py
```

- Stdout is a JSON array holding the batch's one Session ID. Names take
  letters, digits, and hyphens. Repeat `--env KEY=VALUE` per variable; names
  starting with `CANFAR_` are reserved and fail validation.
- `--maxfail F`, from 0 to 1, stops the batch when that fraction of its
  replicas has failed: `0` stops at the first failure, and `0.1` of 64 stops
  at the 7th. Omit it to let every replica run; the batch then ends `Failed`
  if any replica failed.
- The client validates 1 to 256 replicas, 1 to 256 cores, 1 to 512 GB, and 1 to
  28 GPUs per request. Each provider sets its own lower limits, saved per
  Server under `resources` in `canfar server ls -o json`; the CLI also rejects
  values outside the active Server's known `fixed` and `gpus` ranges.
  `--dry-run`, used without `-o`, checks a request against both. A range can
  include sizes the Server does not offer: `canfar.context.Context().resources()`
  lists every fixed size in its `options`. CANFAR's largest Session is 16
  cores and 192 GB.
- For more than 256 workers, split the manifest into parts and submit one
  batch per part, each with its own name and `MANIFEST`, into the same run
  directory. `CANFAR_REPLICA_COUNT` counts one batch's replicas, and the
  run-wide `index` keeps the parts' outputs apart.
- Write the returned ID to the run directory before monitoring. It is the
  run's record and its cleanup scope.
- `CANFAR_TIMEOUT` (seconds, default 30, at most 300) bounds each HTTP
  request, not queue time.
- An empty list means the batch was not confirmed. Reconcile before
  resubmitting: list `canfar ps --all --kind batch -o json`, match this
  request's name, and record a batch that was accepted after its response was
  lost.

```python
import asyncio
import json
from pathlib import Path

from canfar.sessions import AsyncSession

RUN = Path("/arc/projects/PROJECT/runs/RUN")


async def submit(replicas: int) -> list[str]:
    async with AsyncSession(timeout=120) as sessions:
        ids = await sessions.create(
            name=RUN.name,
            image="IMAGE",
            kind="batch",
            cmd="python",
            args=str(RUN / "worker.py"),
            env={"RUN_DIR": str(RUN), "MANIFEST": str(RUN / "manifest.json")},
            replicas=replicas,
            maxfail=0.1,
        )
    (RUN / "attempt-001.json").write_text(
        json.dumps({"ids": ids, "requested": replicas})
    )
    return ids


print(asyncio.run(submit(64)))
```

## 6. Monitor with a budget

A batch's status is `Pending`, `Running`, `Completed`, or `Failed`. One
`canfar ps --all --kind batch -o json`, or `fetch(kind="batch")`, returns each
batch with `id`, `name`, `status`, and `replicas` counts: `total`,
`succeeded`, `failed`, `active`, and `incomplete`. `canfar info SESSION_ID`,
or `info(ids)`, returns the batch document, whose `status.replicas` has one
row per replica with its `id`, `phase`, and `exitCode`. A batch has one log
per replica: `canfar logs SESSION_ID --replica N`, or `logs(ids, replica=N)`,
with `N` counted from 0. Without a replica the Server answers HTTP 400.

Set the deadline from the ramp: items per replica, times the measured time
per item, times three, plus an allowance for queueing, and longer when the
batch runs fewer replicas at once than it has. Poll once a minute. Done when
the batch is `Completed` or `Failed`, missing, or past the deadline. Then save
`info` and the logs of every replica whose `exitCode` is not 0 beside the run:
after a batch finishes, the Server keeps that record only for a retention
period (24 hours), and the outputs are the lasting evidence. At the
deadline, report the replica counts and ask the user whether to keep waiting
or cancel; the batch stays until they answer. A long `Pending` is diagnosed
with `canfar events SESSION_ID` and the table in the
[batch guide](https://www.opencadc.org/canfar/edge/platform/sessions/batch/#monitor-and-troubleshoot).

## 7. Verify, then recover

Compare the outputs against the full manifest and write the pairs without a
valid output to a retry manifest. Done when every manifest item has an output
that passes its check. To recover, fix the cause, wait until the previous
batch is terminal or deleted, then submit the retry manifest as a new batch
under a new name: the worker skips finished outputs. Two batches may share a
run directory only when their manifests are disjoint.

## 8. Clean up

Delete the recorded IDs once the user asks for cleanup; `delete` takes many
IDs per call, and deleting a batch stops all of its replicas:

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
canfar prune RUN batch Completed
canfar prune RUN batch Failed
```

A name containing regex metacharacters is matched as a regular expression, so
quote it, and a short prefix also matches the user's other runs, so use the
full request name.

The batch lifecycle, `--maxfail`, and the replica variables are in the
[batch guide](https://www.opencadc.org/canfar/edge/platform/sessions/batch/#run-many-replicas-as-one-batch).
The complete manifest, worker, submit, verify, and cleanup scripts are in
[Advanced examples](https://www.opencadc.org/canfar/edge/client/advanced-examples/).
Helper edge cases are in [Helpers](https://www.opencadc.org/canfar/edge/client/helpers/),
pipeline sizing in [Best practices](https://www.opencadc.org/canfar/edge/platform/best-practices/),
and lifetime, deadlines, and out-of-memory symptoms in
[Session limits](https://www.opencadc.org/canfar/edge/platform/sessions/limits/).
