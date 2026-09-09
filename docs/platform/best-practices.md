# Best practices for research workflows

Keep the science code independent from the way it is launched. Develop in an
interactive Session, validate on a small input, and run the same command in a
`headless` Session when the workflow is ready for automation.

## Make commands reproducible

- Accept input and output paths as arguments or environment variables.
- Avoid prompts, GUI-only steps, and assumptions about the current directory in
  a headless workflow.
- Record the Container Image, resource request, input identifiers, and code
  revision with each run.
- Write useful progress and error messages to the Session log.
- Give replicas disjoint inputs and use `REPLICA_ID`/`REPLICA_COUNT` or the
  [distributed helpers](../client/helpers.md) to partition work.

```python
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("input", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()

# Load args.input, perform the analysis, and write args.output.
```

## Request measured resources

Start with the flexible request while testing. Once a workload is understood,
request the CPU, memory, and GPU it actually needs. Oversized fixed requests
can wait for matching capacity. Set threaded libraries to the requested CPU
count:

```bash
canfar create \
  --cpu 4 \
  --memory 16 \
  --env OMP_NUM_THREADS=4 \
  headless IMAGE_NAME \
  -- python run.py --input /arc/projects/<project>/input.fits
```

The platform does not promise that many small requests always outrun one large
request. Measure the workload and account for queue time, startup, data
movement, and downstream coordination.

## Separate interactive and batch work

Use a Notebook, Desktop, CARTA, or Firefly Session for exploration and visual
inspection. Use `headless` for unattended reductions and parameter sweeps. Keep
the command-line pipeline free of display dependencies; save a small sample
for visual checks in an interactive Session.

## Plan data movement

- Read data already under `/arc` through its normal path.
- Transfer remote objects once to `/scratch` when a path-oriented tool or
  repeated reads need local files.
- Use an explicit fsspec cache under `/scratch` only when reuse justifies it.
- Write final products, checkpoints, and logs that must survive the Session to
  `/arc` or a persistent VOSpace Service.
- Use unique output names when replicas run concurrently.

See [Storage](storage/index.md), [Data transfers](storage/transfers.md), and
[Filesystem and Python tools](storage/filesystem.md) for the transfer and cache
boundary.

## Keep environments reproducible

Declare Python dependencies in the Container Image or a versioned environment
file. Test imports and command entrypoints before submitting many replicas.
If a runtime installation is necessary, record exactly what was installed and
move stable dependencies into a rebuilt image for the next run. Do not assume
that an example image tag or package is available on every deployment.

When building a custom image:

- start from a documented image available in your registry;
- pin important dependencies and base-image versions where practical;
- keep credentials and large datasets out of the image;
- remove package-manager caches and temporary build files; and
- run the command as a non-root user where the base image supports it.

See [Building Containers](containers/build.md) for the image workflow.

## Checkpoint long workflows

For reductions that can run for hours, split the work into stages and write a
checkpoint after each stage. Make reruns safe: do not overwrite a valid output
unless the command explicitly requests it, and record which inputs completed.
Inspect `canfar events SESSION_ID` and `canfar logs SESSION_ID` when a Session
terminates unexpectedly.

## Related guides

- [Batch processing](sessions/batch.md)
- [Sessions](sessions/index.md)
- [Containers](containers/index.md)
- [Permissions](permissions.md)
- [Support](support/index.md)
