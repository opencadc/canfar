# Batch Processing

Use a `headless` Session when a container should run a command and exit without
an interactive notebook, desktop, CARTA, or Firefly interface.

Batch work uses the same Container Images and storage mounts as interactive
Sessions. The main difference is that you pass a command after `--` in the CLI,
or `cmd` and `args` in Python.

## Submit From the CLI

Authenticate once, then create a headless Session:

```bash
canfar login cadc
canfar create --name data-reduction headless skaha/astroml:latest -- python /arc/projects/myproject/scripts/reduce_data.py
```

Omit resource options for flexible allocation. Use fixed resources only when the
workload has measured requirements:

```bash
canfar create \
  --name large-simulation \
  --cpu 16 \
  --memory 64 \
  headless skaha/astroml:latest \
  -- python /arc/projects/myproject/scripts/simulation.py
```

Pass environment variables with repeated `--env` flags:

```bash
canfar create \
  --name omp-test \
  --env OMP_NUM_THREADS=4 \
  --cpu 4 \
  headless skaha/astroml:latest \
  -- python /arc/projects/myproject/scripts/run.py
```

Create replicas when each container can process an independent slice:

```bash
canfar create \
  --name parameter-study \
  --replicas 10 \
  headless skaha/astroml:latest \
  -- python /arc/projects/myproject/scripts/analyze.py
```

Each replica receives `REPLICA_ID` and `REPLICA_COUNT`. Use those values, or the
helpers in [Distributed Computing](../../client/helpers.md), to split work
deterministically.

`canfar run` and `canfar launch` are compatibility aliases for `canfar create`.
New examples should use `canfar create`.

## Submit From Python

```python
from datetime import datetime

from canfar.sessions import Session

session = Session()
project = "/arc/projects/myproject"
data_path = f"{project}/data/{datetime.now().strftime('%Y%m%d')}"

job_ids = session.create(
    name=f"nightly-reduction-{datetime.now().strftime('%Y%m%d')}",
    image="images.canfar.net/skaha/casa:6.5",
    kind="headless",
    cmd="python",
    args=f"{project}/pipelines/reduce_night.py {data_path}",
)

print(job_ids)
```

Fixed resources use `cores` and `ram`:

```python
job_ids = session.create(
    name="heavy-computation",
    image="images.canfar.net/myproject/processor:latest",
    kind="headless",
    cores=8,
    ram=32,
    cmd="/opt/scripts/heavy_process.sh",
    args="/arc/projects/myproject/data/input.h5 /arc/projects/myproject/results/",
    env={"PROCESSING_THREADS": "8"},
)
```

For async workflows, use `AsyncSession`:

```python
from canfar.sessions import AsyncSession

async with AsyncSession() as session:
    job_ids = await session.create(
        name="async-batch",
        image="images.canfar.net/skaha/astroml:latest",
        kind="headless",
        cmd="python",
        args="/arc/projects/myproject/scripts/analyze.py",
        replicas=10,
    )
```

## Monitor and Clean Up

Use Session IDs returned by `create`:

```bash
canfar ps
canfar info SESSION_ID
canfar events SESSION_ID
canfar logs SESSION_ID
canfar delete SESSION_ID
```

`canfar stats` reports cluster-wide load, not per-Session usage.

Python equivalents:

```python
info = session.info(job_ids)
events = session.events(job_ids)
logs = session.logs(job_ids)
deleted = session.destroy(job_ids)
```

## Resource Guidance

Start flexible. Fixed requests can be harder to schedule and should be based on
measured CPU and memory use.

| Workload | First request |
| --- | --- |
| Script smoke test | Flexible |
| Single-file reduction | Flexible or `cores=1`, `ram=4` |
| Known memory-heavy job | Fixed `cores` and `ram` |
| Independent parameter sweep | Replicas plus modest fixed resources |

Tune threaded libraries to match requested cores:

```bash
canfar create \
  --name threaded-job \
  --cpu 4 \
  --env OMP_NUM_THREADS=4 \
  headless skaha/astroml:latest \
  -- python /arc/projects/myproject/scripts/threaded.py
```

## Storage Rules

Write durable outputs to mounted storage such as `/arc/home/<user>/` or
`/arc/projects/<project>/`. Treat container-local paths as temporary, and treat
`/scratch/` as ephemeral high-speed working space.

## Private Images

Private images require Container Registry credentials. Configure those through
the Python `Configuration` model or the CLI config before submitting the Session;
see the [registry guide](../containers/registry.md).

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Job does not start | `canfar events SESSION_ID` |
| Command exits unexpectedly | `canfar logs SESSION_ID` |
| Resource request waits too long | Try flexible mode or smaller fixed resources |
| Image pull fails | Verify the image name and registry credentials |
| Need structured Session data | `canfar ps --json` |
