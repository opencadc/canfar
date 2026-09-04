---
name: canfar-cvmfs
description: >
  CVMFS on CANFAR: /cvmfs/soft.computecanada.ca Alliance software stack,
  environment modules, read-only lazy mounts, and when to use containers or a
  project environment instead. Use when accessing Alliance software, running
  module load, or diagnosing an empty /cvmfs mount.
---
# CVMFS software

Public guide (orientation only):
[CANFAR CVMFS](https://www.opencadc.org/canfar/latest/platform/cvmfs/)

## What it is

**CernVM File System** — read-only, distributed software trees. Maintained by
**Digital Research Alliance of Canada** on Alliance-backed clusters.

- **Not** writable — install custom packages in a persistent project environment
- **Not** a substitute for project storage
- **Complements** containers: lean image + shared stack on demand

## Deployment note

CVMFS is optional **cluster infrastructure**, not a core Skaha API or a mount
created by the current `science-platform` chart. Confirm it from the live Session
filesystem or the deployment configuration. When mounted, Alliance software is
commonly available at:

```bash
source /cvmfs/soft.computecanada.ca/config/profile/bash.sh
module avail
module load python/3.11
module load gcc openmpi
which python
```

If `/cvmfs` is empty, CVMFS may not be enabled on your site — use container images or project envs instead.

## Lazy mount gotcha

`ls /cvmfs` may look **empty** — repos mount when you access a **known path**:

```bash
ls /cvmfs/soft.computecanada.ca/
```

Always start from documented paths; do not browse `/cvmfs` like `/usr`.

## vs containers

| Approach | When |
| --- | --- |
| **Container image** (Harbor `skaha/*`) | Reproducible stack baked in |
| **CVMFS modules** | Alliance-maintained HPC stack without huge images |
| **pixi/uv/conda on persistent project storage** | Project-specific deps you control |

## Agent rules

1. Never `pip install` into `/cvmfs`.
2. CVMFS cache is **per worker node** — cold start on a new node may be slower.
3. Batch jobs inherit CVMFS when the cluster mounts it.
4. Do not promise CVMFS on a CANFAR/SRCNet site until the live deployment shows it.
