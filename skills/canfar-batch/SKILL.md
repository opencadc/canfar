---
name: canfar-batch
description: >
  CANFAR batch and headless sessions: canfar create headless, pass command after
  --, replicas REPLICA_ID, fixed CPU memory, environment variables, Python Session
  batch jobs. Use for non-interactive processing, parallel jobs, automation,
  production pipelines.
---
# Batch & headless processing

**Headless** sessions run a command and exit — no Notebook, Desktop, or browser UI.
They use the site's Session images and configured persistent mounts. The examples
below use CADC's `/arc/projects` mount; substitute the path shown by your site.

Docs: [Batch processing](https://www.opencadc.org/canfar/latest/platform/sessions/batch/)

## CLI

```bash
canfar login cadc

# Flexible resources (default)
canfar create headless skaha/astroml:latest --name reduce \
  -- python /arc/projects/mygroup/scripts/reduce.py

# Fixed resources
canfar create headless skaha/astroml:latest --name sim --cpu 16 --memory 64 \
  -- python /arc/projects/mygroup/scripts/simulation.py

# Environment variables
canfar create headless skaha/astroml:latest --name omp-test --cpu 4 \
  --env OMP_NUM_THREADS=4 -- python /arc/projects/mygroup/run.py

# Parallel replicas (independent slices, client max 512)
canfar create headless skaha/astroml:latest --name study --replicas 10 \
  -- python /arc/projects/mygroup/analyze.py
```

Each replica gets `REPLICA_ID` and `REPLICA_COUNT` — use them for deterministic
splits. This behavior is defined by the current `canfar` client and Skaha Session
templates; do not infer it from an older documentation example.

`canfar run` and `canfar launch` are aliases for `canfar create`.

Headless Sessions do not count toward Skaha's interactive Session cap. The
current headless Job template has a 14-day deadline, but deployment queue and
resource policy still determine what actually runs.

## Python client

```python
from canfar.sessions import Session

session = Session()
ids = session.create(
    name="nightly-reduction",
    image="images.canfar.net/skaha/astroml:latest",
    kind="headless",
    cmd="python",
    args="/arc/projects/mygroup/pipelines/reduce.py",
    cores=8,
    ram=32,
    replicas=10,
)
print(ids)
```

Async: `AsyncSession` + `await session.events(ids, verbose=True)` — see `canfar-python-client`.

## Data paths

- Put input/output on the site's persistent project mount so replicas and
  collaborators can read it (CADC example: `/arc/projects/…`).
- `/scratch` belongs to one replica Session and is not shared with other replicas.

## Best practices

See `canfar-best-practices` — prefer many small parallel jobs over one huge container.
