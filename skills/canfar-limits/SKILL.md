---
name: canfar-limits
description: >
  CANFAR Session resource limits: cgroup CPU/memory, ephemeral storage, GPU,
  live Context resources, flexible vs fixed allocation, and the per-user
  interactive Session cap. Use when OOM, throttled, queued, or asking how much
  CPU, RAM, GPU, or scratch a Session has.
---
# Session limits

## Inspect the live Session

```bash
canfar info <session-id>
nproc
free -h
df -h /scratch
cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null
nvidia-smi   # only when a GPU was allocated
canfar stats # platform capacity, not this Session's cgroup
```

Portal Session details and `canfar info` show requested CPU/RAM/GPU. For
programmatic choices, query the selected Server rather than hard-coding values:

```python
from canfar.context import Context
print(Context().resources())
```

## Implementation defaults, not user guarantees

The current `science-platform` chart/templates provide these reference defaults:

| Setting | Current implementation default | Verify live with |
| --- | --- | --- |
| Interactive Session lifetime | 4 days (`expirySeconds: 345600`) | Portal / `canfar info` |
| Headless deadline | 14 days in the headless Job template | `canfar info` / events |
| Active interactive Sessions | 5 per user | create error / Portal |
| Non-desktop ephemeral ceiling | 200 GiB | `df -h /scratch` |
| Desktop ephemeral storage | Separate smaller Job template value | `df -h /scratch` |
| Flexible CPU/RAM | Site resource policy + live Context | `Context().resources()` |

Operators can override the chart settings, queue policy, resource limits, GPU pools,
and node capacity. Do not promise these values to a user.

Headless creates and existing desktop-app Sessions (in-Desktop software, not
Desktop itself) are exempt from Skaha's interactive Session-count check. Desktop
sessions still count. The current client accepts at most 512 replicas in one
request, but a deployment or queue can accept fewer in practice.

## Flexible versus fixed

| Mode | When |
| --- | --- |
| Flexible | Exploration; site policy supplies request and limit |
| Fixed (`--cpu`, `--memory`, `--gpu`) | Measured work needing a specific allocation |

```bash
canfar create notebook skaha/astroml:latest --cpu 4 --memory 16
```

A larger fixed request can wait longer in the site queue or fail if the site does
not offer that combination. Check `canfar events <id>`.

## OOM, disk full, or quota

| Symptom | Likely boundary | Action |
| --- | --- | --- |
| Process killed / exit 137 | cgroup memory | Smaller chunks or measured fixed memory |
| `No space left` on `/scratch` | Session ephemeral storage | Remove temporary files; persist results |
| Save/login fails in home | Persistent-home quota | `canfar-quotas` |
| Pending after fixed request | Queue/capacity/image pull | `canfar events <id>` and `canfar stats` |

Scratch full, home quota, and cluster capacity are different problems.

## Agent rules

1. Distinguish requested resources, cgroup limits, platform capacity, and storage quotas.
2. Use the live Context/Portal before recommending a resource value.
3. For independent work, prefer headless replicas over one impractically large Session.
4. `/scratch` may survive an **interactive** container restart; headless Jobs do
   not restart. Session delete/expiry always wipes it.
