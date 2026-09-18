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
| Interactive Session lifetime | 4 days | `canfar info SESSION_ID` shows the expiry time |
| `headless` Session deadline | 14 days | A failed command is not restarted |
| Finished `headless` Session record | Kept for 1 hour | The ID then leaves `canfar ps --all`; judge the run by its outputs |
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

A fixed request can stay `Pending` longer than a flexible one, because it waits
for a node with that much free capacity. `canfar events SESSION_ID` shows what
a Pending Session is waiting for; see [Batch processing](batch.md#monitor-and-troubleshoot).

## What a running Session really has

Inside the Session, ask the container:

```bash title="Terminal inside your Session"
nproc
free -h
cat /sys/fs/cgroup/memory.max
df -h /scratch
nvidia-smi
```

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
