# Session limits and resources

Every Session on the Science Platform runs inside a container with either
**flexible** or **fixed** resource allocation.

- **Flexible allocation.** This is the default when you launch a Session without
  `--cpu` or `--memory`. The Server grants a small guaranteed baseline so your
  Session starts without waiting for a dedicated reservation, and the Session
  can burst to a higher ceiling when cluster capacity is free. Use flexible
  allocation for interactive exploration, development, and prototyping.
- **Fixed allocation.** Pass `--cpu` and `--memory` from the sizes the Server
  offers when your workload needs a guaranteed reservation. Fixed Sessions can
  stay `Pending` longer while the cluster schedules a node with that free
  capacity.

CANFAR runs at the Canadian Astronomy Data Centre (CADC) and at regional
centres across the SKA Regional Centre Network (SRCNet), so these limits vary
by deployment. Platform administrators configure the flexible baseline, burst
ceilings, and fixed sizes on each Science Platform Server.

---

<span id="what-your-server-offers"></span>

## What your Server offers

The CLI and the Python library read the active Server's limits from its context
endpoint.

### Check limits with the CLI

Run `canfar server ls` to inspect the resource ranges configured for each Server
available to your active Identity Provider (IDP):

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

- **Flexible** (`1-16 cores`, `4-32 GB`) shows the guaranteed share and burst
  ceiling. A flexible Session is guaranteed 1 core and 4 GB RAM, and can burst
  up to 16 cores and 32 GB RAM when capacity allows.
- **Fixed** (`1-16 cores`, `1-192 GB`) shows the smallest and largest fixed
  requests accepted.
- **GPUs** (`1-28`) shows the accepted GPU counts, or `none`.
- **Sessions** (`5`) shows the maximum concurrent interactive Sessions per user.
  `headless` batch Sessions do not count toward this limit.

You can also check the active Server's limits with `canfar create --help`. The
help text narrows the `--cpu`, `--memory`, and `--gpu` options to the values
your Server supports and shows the flexible burst ceiling as the default:

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
accepted ranges so out-of-range values exit with code 2 before sending an HTTP
request. The Server can still reject a fixed request within those bounds if the
value is not one of the Server's advertised `options`.

Test request syntax and limits without launching a container by adding
`--dry-run`:

```bash
canfar create headless skaha/astroml:latest --cpu 8 --memory 32 --replicas 100 --dry-run
```

When you pass `--replicas` greater than 1, the Server names the Sessions
`NAME-1` to `NAME-N` and sets `REPLICA_ID` (1-based) and `REPLICA_COUNT` in
each container. See [distributed helpers](../../client/helpers.md).

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

`Pending` and `Running` interactive Sessions count toward your per-user limit,
which is 5 by default. Batch `headless` Sessions and child applications opened
inside a Desktop Session do not count toward this quota. If you reach your
limit, list your running Sessions and delete any you no longer need:

```bash
canfar ps
canfar delete SESSION_ID
```

To keep an interactive Session past its expiry time, renew it before it
expires from the Science Portal, with `canfar renew SESSION_ID`, or with
[`Session.renew()`](../../client/session.md#renew-an-interactive-session). The
CLI and Python renewal methods are available in v1.5.0 and later. Renewal
resets the lifetime.

### Scheduling and queue times

Fixed requests need a node with the full requested CPU and memory free at the
same time. When the cluster is busy, a large fixed request stays `Pending`
until capacity frees up. Inspect its scheduling events to see why it is waiting:

```bash
canfar events SESSION_ID
```

See [Batch processing](batch.md#monitor-and-troubleshoot) for queue
troubleshooting.

---

<span id="threads-follow-the-request"></span>

## Threads follow the request

To prevent CPU contention on shared nodes, the Science Platform sets
`OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, and
`JULIA_NUM_THREADS` to the number of cores you requested.

In a flexible Session, you did not request a fixed core count, so the Server
sets these variables to the guaranteed baseline, usually `1`, even though the
container can burst up to 16 cores.

If your code uses threaded libraries such as NumPy, SciPy, OpenBLAS, or Julia
in a flexible Session, check the environment variable:

```bash
echo $OMP_NUM_THREADS
```

To use burst CPU capacity in a flexible Session, set the thread variables
explicitly:

- In a `headless` Session, pass `--env OMP_NUM_THREADS=4` or your chosen thread count.
- In a Jupyter notebook or interactive terminal, set the variable before
  importing numerical libraries:
  ```python
  import os

  os.environ["OMP_NUM_THREADS"] = "4"
  ```

---

## What a running Session really has

Check the container's granted limits and available storage from inside the
Session terminal:

```bash title="Terminal inside your Session"
nproc
free -h
cat /sys/fs/cgroup/memory.max
df -h /scratch
nvidia-smi
```

- `/scratch` is fast Session-local temporary storage. It survives container
  restarts of an interactive Session, and the Server deletes it when the
  Session is deleted. Write persistent results to mounted `/arc` storage or a
  VOSpace Service.
- `cat /sys/fs/cgroup/memory.max` prints the cgroup memory limit in bytes.
  `max` means unlimited. Older Linux kernels use
  `/sys/fs/cgroup/memory/memory.limit_in_bytes`.
- `nvidia-smi` works only when the Session requested a GPU and the Container
  Image includes the NVIDIA tools.
- `canfar info SESSION_ID` shows the Session's requested resources and current
  usage. `canfar stats` shows platform-wide capacity and allocation.

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
