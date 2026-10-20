# Session limits and resources

Every Session on the Science Platform runs inside a container governed by one of
two resource allocation models: **flexible** or **fixed**. Understanding how
these models work, who configures them, and how to inspect them lets you size
your workload efficiently without waiting unnecessarily in job queues.

- **Flexible allocation (the default):** When you launch a Session without
  requesting `--cpu` or `--memory`, the Server grants a modest guaranteed
  baseline so your Session starts immediately. When cluster capacity is
  available, the Session can dynamically burst up to a higher ceiling.
  Flexible allocation is optimal for interactive exploration, development, and
  prototyping.
- **Fixed allocation:** When your pipeline requires guaranteed, non-preemptible
  compute or predictable execution times, you can request explicit `--cpu` and
  `--memory` values from the specific sizes the Server offers. Fixed Sessions
  may wait longer in a `Pending` state while the platform schedules a host with
  sufficient dedicated capacity.

Because CANFAR powers diverse astronomical deployments—from the primary
Canadian Astronomy Data Centre (CADC) facility to regional centres across the
SKA Regional Centre Network (SRCNet)—these limits are not uniform. **Local
platform administrators configure the flexible baseline, burst ceilings, and
supported fixed sizes for each Science Platform Server.**

---

<span id="what-your-server-offers"></span>

## What your Server offers

You do not need to guess what resources are available on your active Server. The
CLI and the Python library query the Server's context capabilities directly.

### Check limits with the CLI

Run `canfar server ls` to inspect the resource ranges configured by local
platform administrators for each Server available to your active Identity
Provider (IDP):

```bash
canfar server ls
```

```text
                                          Known Servers

  Name     URI / URL                        Version   Flexible     Fixed        GPUs   Sessions
 ───────────────────────────────────────────────────────────────────────────────────────────────
  canfar   ivo://cadc.nrc.ca/skaha          v1        1-16 cores   1-16 cores   1-28   5
           https://ws-uv.canfar.net/skaha             4-32 GB      1-192 GB

Flexible resources allow dynamic allocation based on availability.
Fixed resources guarantee allocation.
Sessions limit per user.
```

In this output from the CADC-maintained Science Platform:

- The **Flexible** column (`1-16 cores`, `4-32 GB`) shows the guaranteed share
  to burst ceiling: a flexible Session is guaranteed 1 core and 4 GB RAM, and
  can burst up to 16 cores and 32 GB RAM when capacity allows.
- The **Fixed** column (`1-16 cores`, `1-192 GB`) shows the minimum and maximum
  fixed requests accepted.
- The **GPUs** column (`1-28`) shows available GPU bounds (or `none`).
- The **Sessions** column (`5`) shows the maximum concurrent interactive
  Sessions per user (`headless` batch Sessions do not count against this
  limit).

You can also check the active Server's limits with `canfar create --help`. The
help text dynamically narrows the `--cpu`, `--memory`, and `--gpu` options to
the values your Server supports, displaying the flexible burst ceiling as the
default:

```text
--cpu INTEGER RANGE [1<=x<=16] [default: flexible ≤ 16]
--memory INTEGER RANGE [1<=x<=192] [default: flexible ≤ 32]
```

### Inspect structured metadata

In automated workflows and Python scripts, you can inspect the exact limits
programmatically. `canfar server ls -o json` outputs the structured `resources`
model, which corresponds to [`Context().resources()`](../../client/context.md):

```yaml
resources:
  flexible:                    # Applied when omitting --cpu and --memory
    cores: {min: 1, max: 16}   # defaultRequest to defaultLimit
    ram: {min: 4, max: 32}     # GB
  fixed:                       # Applied when passing --cpu and --memory
    cores: {min: 1, max: 16}   # Smallest to largest supported option
    ram: {min: 1, max: 192}
  gpus: {min: 1, max: 28}      # {min: 0, max: 0} when none are offered
  sessions: 5                  # Concurrent interactive Sessions per user
```

The underlying context endpoint reports three key fields for compute resources:

| Field | Meaning |
| --- | --- |
| `defaultRequest` | What a flexible Session is guaranteed at launch. |
| `defaultLimit` | The burst ceiling a flexible Session can reach when unused cluster capacity is free. |
| `options` | The discrete values a fixed request may name; the largest option marks the biggest fixed Session the Server runs. |

If a Server does not advertise a particular capability, the value appears as
`unknown` in the CLI and `null` in JSON.

---

## What the client accepts

When you request a Session, the client validates your parameters locally
before contacting the remote platform:

| Request | Accepted values |
| --- | --- |
| `--cpu` / `cores` | 1 to 256 cores |
| `--memory` / `ram` | 1 to 512 GB |
| `--gpu` / `gpu` | 1 to 28 GPUs |
| `--replicas` / `replicas` | 1 to 256; exactly 1 for `desktop` and `firefly` |
| Command, arguments, `--env` | `headless` Sessions only |
| `--name` | Letters, digits, and hyphens |

`desktop` and `firefly` interactive applications use pre-configured container
profiles set by the Server; explicit `--cpu` and `--memory` parameters are
ignored for them.

When the active Server's limits are known, `canfar create` narrows its
acceptable ranges so that out-of-bounds requests fail fast (with exit code 2)
before submitting any HTTP requests. A request within the general boundaries
can still be rejected by the Server if a fixed request does not match one of
the Server's advertised `options`.

You can test request syntax and limits safely without launching any containers
by adding `--dry-run`:

```bash
canfar create headless skaha/astroml:latest --cpu 8 --memory 32 --replicas 100 --dry-run
```

When creating replicated Sessions (`--replicas > 1`), instances are named
`NAME-1` to `NAME-N`. Each container receives `REPLICA_ID` (1-indexed) and
`REPLICA_COUNT` environment variables to simplify data partitioning; see
[distributed helpers](../../client/helpers.md).

---

## What the Server enforces

Once accepted, your container runs under platform policies enforced by the
Server and the underlying cluster. The open-source
[Science Platform](https://github.com/opencadc/science-platform) defaults
provide a general baseline, but remember that local platform administrators
may adjust them:

| Policy | Default | How it shows up |
| --- | --- | --- |
| Flexible resources (no `--cpu` or `--memory`) | 1 core and 4 GB guaranteed, bursting to 8 cores and 32 GB; CANFAR bursts to 16 cores | The Session starts with minimal reservation and shares burst capacity with other users |
| Fixed resources (`--cpu` and `--memory`) | The request is also the limit | The values must be among the Server's `options`; on CANFAR at most 16 cores and 192 GB |
| `desktop` and `firefly` sizes | Set by the Server | `--cpu` and `--memory` are ignored |
| Interactive Session lifetime | 4 days | `canfar info SESSION_ID` shows the expiry time |
| `headless` Session deadline | 14 days | A failed command is not restarted |
| Finished Session record | Kept for 1 hour (`headless`) or 1 day (interactive) | The ID then leaves `canfar ps --all`; judge a run by its outputs |
| Active interactive Sessions per user | 5 | `create` is rejected with "has reached the maximum of N active sessions" |
| Session-local storage, including `/scratch` | 20 GiB to start, growing to 200 GiB | `No space left on device`; `desktop` Sessions get a smaller amount |

### Managing your active Session quota

`Pending` and `Running` interactive Sessions count toward your per-user limit
(typically 5). Batch `headless` Sessions and sub-processes inside an existing
Desktop session do not count against this quota. If you reach your limit, check
running Sessions and delete any you no longer need:

```bash
canfar ps
canfar delete SESSION_ID
```

To keep an interactive Session past its expiry time, renew it before it
expires from the Science Portal, with `canfar renew SESSION_ID`, or with
[`Session.renew()`](../../client/session.md#renew-an-interactive-session)
(the CLI and Python options are unreleased). Renewal resets the lifetime.

### Scheduling and queue times

Fixed requests must be scheduled onto nodes that have the full requested CPU
and memory immediately unreserved. If the cluster is busy, a large fixed
request will remain `Pending` until resources clear. If a Session is waiting,
inspect its scheduling events to see why:

```bash
canfar events SESSION_ID
```

See [Batch processing](batch.md#monitor-and-troubleshoot) for detailed queue
investigation workflows.

---

<span id="threads-follow-the-request"></span>

## Threads follow the request

To prevent unintended CPU contention on shared nodes, the Science Platform
automatically initializes thread limit environment variables—specifically
`OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, and
`JULIA_NUM_THREADS`—to the number of cores you requested.

In a **flexible** Session, because you did not specify cores, the Server sets
these variables to the guaranteed base allocation—typically **`1`** core—even
though your container can burst up to 16 cores.

If your code uses multi-threaded libraries (like NumPy, SciPy, OpenBLAS, or
Julia) in a flexible Session, check the environment variable:

```bash
echo $OMP_NUM_THREADS
```

To take advantage of burst CPU capacity in a flexible Session, set the thread
variables explicitly:

- In a `headless` Session, pass `--env OMP_NUM_THREADS=4` (or your chosen burst level).
- In a Jupyter notebook or interactive terminal, set the variable before
  importing numerical libraries:
  ```python
  import os

  os.environ["OMP_NUM_THREADS"] = "4"
  ```

---

## What a running Session really has

You can verify the container's granted limits and available storage from inside
the Session terminal:

```bash title="Terminal inside your Session"
nproc
free -h
cat /sys/fs/cgroup/memory.max
df -h /scratch
nvidia-smi
```

Key points about container resources:

- `/scratch` provides high-speed, Session-local temporary storage. It survives
  in-place container restarts of interactive Sessions, but is permanently
  purged when the Session is deleted. Always write persistent results to
  mounted `/arc` storage or remote VOSpace services.
- `cat /sys/fs/cgroup/memory.max` reports the cgroup memory limit in bytes
  (`max` means unlimited; older Linux kernels use
  `/sys/fs/cgroup/memory/memory.limit_in_bytes`).
- `nvidia-smi` is available only when a GPU was explicitly allocated and the
  container image includes the compatible GPU drivers and runtime.
- `canfar info SESSION_ID` displays what was requested and current usage,
  whereas `canfar stats` provides aggregate platform-wide metrics.

---

<span id="read-the-symptom"></span>

## Read the symptom

When a Session fails, its exit status and logs usually indicate which limit was
exceeded. Use this table to diagnose the boundary and choose the appropriate fix:

| Symptom | Boundary reached | Next step |
| --- | --- | --- |
| Process `Killed`, or exit code 137 | Container memory limit exceeded | Process smaller data chunks, or request an explicit fixed memory size |
| `No space left on device` under `/scratch` | Session-local storage full | Clean up intermediate files or write outputs directly to `/arc` |
| Saving or logging in fails under `/arc/home` | Persistent storage quota reached | [Check usage and request space](../storage/index.md#checking-quotas-and-requesting-more-space) |
| `create` rejected for maximum active sessions | Per-user interactive limit reached | Delete completed or idle Sessions using `canfar delete SESSION_ID` |
| Session remains in `Pending` state | Cluster capacity waiting or image pulling | Run `canfar events SESSION_ID`; consider a flexible request or smaller fixed size |

## Related guides

- [Sessions overview](index.md)
- [Batch processing](batch.md)
- [Best practices](../best-practices.md)
- [Storage](../storage/index.md)
