---
name: canfar-best-practices
description: >
  CANFAR pipeline best practices: batch-friendly code, scale out many small jobs,
  argparse env vars, no GUI in batch, OMP_NUM_THREADS, horizontal scaling,
  reproducible containers. Use when designing pipelines, production processing,
  parallel workloads, resource sizing.
---
# Best practices

User guide: [Best practices](https://www.opencadc.org/canfar/latest/platform/best-practices/)

## Batch-friendly code

- No GUI, no `input()` — runs unattended in headless sessions
- Paths via **CLI args or env vars**, never hard-coded:

```python
import argparse, os
parser = argparse.ArgumentParser()
parser.add_argument("--input", default=os.getenv("INPUT_FILE"))
parser.add_argument("--output_dir", default=os.getenv("OUTPUT_DIR", "."))
args = parser.parse_args()
```

- Same script in Jupyter (debug) and batch (scale) — export notebook with `jupyter nbconvert --to script`

## Scale out, not up

| Prefer | Avoid |
| --- | --- |
| 100 × (1 CPU, 4 GB) parallel jobs | 1 × (100 CPU, 400 GB) monolith |
| `--replicas N` or many `canfar create` | One giant session |

This is a workload-shape heuristic, not a capacity promise. Query the live
Context/queue and choose chunk sizes that can retry independently.

## Right-size resources

1. Prototype in **flexible** mode
2. Measure memory/CPU
3. Request fixed `--cpu` / `--memory` only when needed

## Threading

If job requests 4 cores:

```bash
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
```

## Storage

- Input catalog on the site's persistent **project storage**
- Stage hot files to **`/scratch`** per session
- Results back to persistent project storage or a suitable VOSpace Service

## Containers

Pin the full image URI and preferably digest in scripts/workflow metadata.

Related: `canfar-batch`, `canfar-containers`, `canfar-limits`
