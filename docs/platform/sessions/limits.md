# Session limits and resources

Three layers bound a Session: the client validates the request, the Science
Platform Server applies its policy, and the running container enforces what
was granted. Check the layer that matches your question before changing a
request.

## What the client accepts

`canfar create` and `Session.create()` validate a request before sending it:

| Request | Accepted values |
| --- | --- |
| `--cpu` / `cores` | 1 to 256 cores |
| `--memory` / `ram` | 1 to 512 GB |
| `--gpu` / `gpu` | 1 to 28 GPUs |
| `--replicas` / `replicas` | 1 to 512; exactly 1 for `desktop` and `firefly` |
| Command, arguments, `--env` | `headless` Sessions only |
| `--name` | Letters, digits, and hyphens |

`desktop` and `firefly` Sessions use the Server's own sizes, so CPU and memory
values are ignored for them. Check a request without creating anything:

```bash
canfar create headless skaha/astroml:latest --cpu 8 --memory 32 --replicas 100 --dry-run
```

Passing these checks does not mean the Server offers that combination. Query
the live options with [`Context.resources()`](../../client/context.md), and
omit `--cpu` and `--memory` to let the Server apply its flexible policy.

With more than one replica, Sessions are named `NAME-1` to `NAME-N`, and each
container receives `REPLICA_ID` (starting at 1) and `REPLICA_COUNT`. See the
[distributed helpers](../../client/helpers.md).

## What the Server enforces

These are the defaults of the open-source
[Science Platform](https://github.com/opencadc/science-platform). An operator
can change every one of them, so treat them as orientation and confirm the
values that matter to your project with [support](../support/index.md).

| Policy | Default | How it shows up |
| --- | --- | --- |
| Flexible resources (no `--cpu` or `--memory`) | 1 core and 4 GB guaranteed, bursting to 8 cores and 32 GB | The Session starts on little free capacity and shares the burst with other users |
| Fixed resources (`--cpu` and `--memory`) | The request is also the limit | The values must be among the Server's offered options |
| `desktop` and `firefly` sizes | Set by the Server | `--cpu` and `--memory` are ignored |
| Interactive Session lifetime | 4 days | `canfar info SESSION_ID` shows the expiry time |
| `headless` Session deadline | 14 days | A failed command is not restarted |
| Finished Session record | Kept for 1 hour (`headless`) or 1 day (interactive) | The ID then leaves `canfar ps --all`; judge a run by its outputs |
| Active interactive Sessions per user | 5 | `create` is rejected with "has reached the maximum of N active sessions" |
| Session-local storage, including `/scratch` | 20 GiB to start, growing to 200 GiB | `No space left on device`; `desktop` Sessions get a smaller amount |

`Pending` and `Running` Sessions count toward the per-user limit. `headless`
Sessions and applications started inside a Desktop do not, so replicated batch
work is not blocked by your interactive Sessions. When you reach the limit,
list your Sessions and delete one you no longer need:

```bash
canfar ps
canfar delete SESSION_ID
```

The Server's API can renew an interactive Session, which resets its remaining
lifetime to the full period. The `canfar` client does not offer that action
yet, so save your work and start a new Session before the expiry time.

A fixed request can stay `Pending` longer than a flexible one, because it waits
for a node with that much free capacity. `canfar events SESSION_ID` shows what
a Pending Session is waiting for; see [Batch processing](batch.md#monitor-and-troubleshoot).

## Threads follow the request

The Server sets `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
and `JULIA_NUM_THREADS` to the number of cores you requested, so numerical
libraries do not start more threads than the Session was granted. A flexible
Session requests one core, so there these variables are `1` even though the
Session can burst to more. To use the burst, set them yourself: pass
`--env OMP_NUM_THREADS=4` to a `headless` Session, or export the variable in a
notebook or terminal before the library is imported.

## What a running Session really has

Inside the Session, ask the container:

```bash title="Terminal inside your Session"
nproc
free -h
cat /sys/fs/cgroup/memory.max
df -h /scratch
nvidia-smi
```

`/scratch` lasts as long as the Session. It survives an in-place restart of an
interactive Session's container and is removed when the Session ends; a
`headless` command is never restarted.

`memory.max` is the memory limit in bytes (`max` means unlimited); on older
hosts the file is `/sys/fs/cgroup/memory/memory.limit_in_bytes`. `nvidia-smi`
is present only when a GPU was granted and the image supports the Server's GPU
stack. `canfar info SESSION_ID` shows what was requested and what is in use;
`canfar stats` describes the whole Server, not your Session.

## Read the symptom

| Symptom | Boundary reached | Next step |
| --- | --- | --- |
| Process `Killed`, or exit code 137 | The container's memory limit | Process smaller pieces, or request measured fixed memory |
| `No space left on device` under `/scratch` | Session-local storage | Remove intermediates and move results to `/arc` |
| Saving or logging in fails under `/arc/home` | Persistent storage quota | [Check usage and request space](../storage/index.md#checking-quotas-and-requesting-more-space) |
| `create` rejected for the maximum active sessions | Per-user interactive limit | Delete a Session you no longer need |
| `Pending` after a fixed request | Server capacity or an image pull | `canfar events SESSION_ID`, then a smaller or flexible request |

## Related guides

- [Sessions](index.md)
- [Batch processing](batch.md)
- [Best practices](../best-practices.md)
- [Storage](../storage/index.md)
