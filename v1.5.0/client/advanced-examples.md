# Advanced Examples

Run a small FITS metadata pipeline, check every output, and recover missing
work before scaling up. This example writes one JSON summary per input file.
Replace the header-reading step with your tested reduction when you are ready.

<span id="advanced-resource-allocation-strategies"></span>
<span id="mixed-resource-allocation"></span>
<span id="resource-allocation-guidelines-for-advanced-workflows"></span>
<span id="best-practices"></span>

## Before you start

Run the controller scripts in a Notebook or Desktop Session with access to
your project under `/arc`. The worker Sessions must be able to read those same
paths. These examples do not assume that `/arc` is mounted on your laptop.

- Follow [client setup](get-started.md#install) and authenticate in the environment
  running the controller.
- Choose a headless image containing Python, `astropy`, and `canfar`. List images
  with `canfar image ls --kind headless`; a registry listing alone does not
  establish which Python packages an image contains. The platform's standard
  images, such as `skaha/astroml`, ship the `canfar` client, which can be a
  release or two behind; run `canfar version` in the image when the worker
  depends on a recent feature.
- Test the worker on one FITS file using that image before a larger run.
  Use a versioned image tag and record it; avoid a mutable `latest` tag for
  a reproducible pipeline.
- Keep the input files, image, worker script, and manifest unchanged within a
  run. Start a new run directory when any of them changes.

!!! note "Start small"

    Submit one worker first. Try two replicas on a small dataset after that
    succeeds, then choose a larger count based on measured resources and
    platform capacity. Replicas are requests; they need not start together.

## 1. Record the inputs and run settings

In your Session terminal, choose a new run directory and an available image.
Replace `PROJECT` and the example image before running these commands:

```bash title="Terminal inside your Session"
export RUN_DIR=/arc/projects/PROJECT/runs/fits-summary-001
export CANFAR_WORKFLOW_IMAGE=images.canfar.net/PROJECT/analysis:VERSION
```

Save this as `prepare.py`. Replace the input directory and run it once with
`python prepare.py`. Start with a directory containing one small FITS file.

```python title="prepare.py" hl_lines="7 11"
import json
import os
from pathlib import Path

run = Path(os.environ["RUN_DIR"])
inputs = sorted(
    str(path.resolve())
    for path in Path("/arc/projects/PROJECT/observations").glob("*.fits")
)
if not inputs:
    raise SystemExit("No FITS inputs found; check the directory.")
run.mkdir(parents=True, exist_ok=False)
(run / "results").mkdir()
(run / "manifest.json").write_text(json.dumps(inputs, indent=2))
(run / "run.json").write_text(json.dumps({
    "image": os.environ["CANFAR_WORKFLOW_IMAGE"],
    "input_count": len(inputs),
}, indent=2))
print(f"Recorded {len(inputs)} inputs in {run}")
```

The ordered manifest gives every replica the same input list. Enumerating a
directory independently in each worker can produce different orders or include
files added during the run.

<span id="distributed-processing-strategies"></span>
<span id="chunking-distributedchunk"></span>
<span id="striping-distributedstripe"></span>
<span id="real-world-example-processing-astronomical-data"></span>
<span id="partition-work-inside-a-container"></span>

<span id="when-to-use-each-strategy"></span>

## 2. Save and test the worker

Save the following script as `$RUN_DIR/summarize_fits.py`. Each replica reads
its share of the manifest using `chunk()`. Output names use manifest positions,
so inputs with identical basenames cannot overwrite each other.

```python title="summarize_fits.py" hl_lines="12 24"
import json
import os
from pathlib import Path

from astropy.io import fits
from canfar.helpers.distributed import chunk

run = Path(os.environ["RUN_DIR"])
inputs = json.loads((run / "manifest.json").read_text())
for index, source in chunk(list(enumerate(inputs))):
    target = run / "results" / f"{index:06d}.json"
    if target.exists():
        previous = json.loads(target.read_text())
        if previous["input"] != source or "axes" not in previous or "object" not in previous:
            raise RuntimeError(f"Invalid existing result: {target}")
        continue
    header = fits.getheader(source)
    result = {
        "input": source,
        "object": str(header.get("OBJECT", "")),
        "axes": [header.get(f"NAXIS{i}", 0)
                 for i in range(1, header.get("NAXIS", 0) + 1)],
    }
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(result))
    temporary.replace(target)
    print(f"Wrote {target}", flush=True)
```

`REPLICA_ID` is one-based; `REPLICA_COUNT` is the number requested. CANFAR
supplies both to headless Sessions. The helper defaults to one worker when
they are absent. For a local smoke check in your interactive Session:

```bash title="Terminal inside your Session"
REPLICA_ID=1 REPLICA_COUNT=1 python "$RUN_DIR/summarize_fits.py"
```

Inspect the JSON result and compare it with the input FITS header. Then prepare
a **new run directory** for the headless test, copying the tested worker into
it. Existing results are deliberately skipped when you resume the same run.

`stripe()` is an alternative that distributes every Nth manifest item.
Both helpers require all workers to see the same ordered inputs. For remote
inputs, first [stage the files](data.md#materialize-a-local-file) or adapt the
worker using the documented synchronous filesystem API.

<span id="process-a-vospace-service-in-each-replica"></span>

<span id="massively-parallel-processing"></span>
<span id="large-scale-parallel-processing"></span>
<span id="replicated-headless-processing"></span>

## 3. Submit and monitor an attempt

Save this as `submit.py` in your controller's working directory. It records
accepted IDs before monitoring, checks for partial submission, and saves
diagnostics. The monitoring budget stops new polling after 30 minutes; an
in-flight HTTP request can still take its configured timeout.

```python title="submit.py" hl_lines="20 32"
import json
import os
import sys
import time
from pathlib import Path

from canfar.sessions import Session

run = Path(os.environ["RUN_DIR"])
settings = json.loads((run / "run.json").read_text())
attempt = sys.argv[1]                 # e.g. attempt-001
replicas = int(sys.argv[2])            # start with 1
record = run / f"{attempt}.json"
name = f"{run.name}-{attempt}"
terminal = {"Completed", "Succeeded", "Error", "Failed"}

with record.open("x") as saved, Session() as session:
    ids = session.create(
        name=name,
        image=settings["image"],
        kind="headless",
        cmd="python",
        args=str(run / "summarize_fits.py"),
        env={"RUN_DIR": str(run)},
        replicas=replicas,
    )
    json.dump({"name": name, "ids": ids, "requested": replicas}, saved, indent=2)
    saved.flush()
    print(f"Accepted {len(ids)} of {replicas} requested Sessions: {ids}")
    if len(ids) != replicas:
        print("Partial submission: verify all outputs before retrying.")
    if not ids:
        raise SystemExit("No accepted IDs; inspect the creation errors.")

    deadline = time.monotonic() + 1800
    while time.monotonic() < deadline:
        details = session.info(ids)
        states = {item.get("id"): item.get("status") for item in details}
        print(states, flush=True)
        if all(states.get(value) in terminal for value in ids):
            break
        time.sleep(10)
    else:
        print("Polling budget expired; Sessions may still be running.")

    diagnostics = {
        "details": session.info(ids),
        "events": session.events(ids),
        "logs": session.logs(ids),
    }
    (run / f"{attempt}-diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2)
    )
```

Use paths without whitespace for this example's worker command. Submit a
single worker, then use a new attempt name when you intentionally retry:

```bash title="Terminal inside your controller Session"
python submit.py attempt-001 1
```

An accepted ID is not proof of completion. Missing `info()` records are not
treated as successful; individual failed requests can be omitted by the client.
`Pending` may reflect admission, resources, image pulling, or initialization.
See [batch troubleshooting](../platform/sessions/batch.md#monitor-and-troubleshoot).

!!! warning "Do not blindly resubmit an interrupted attempt"

    The attempt file is created before submission and cannot be overwritten by
    this script. If the controller stops before saving IDs, inspect
    `canfar ps --all` and the recorded run/attempt name to find Sessions that
    may have been accepted. An HTTP failure can also leave acceptance uncertain.
    Reconcile those Sessions before retrying.

<span id="common-issues"></span>

## 4. Verify outputs and recover missing work

Run this in the controller environment after the attempt has stopped:

```python title="verify_outputs.py"
import json
import os
from pathlib import Path

run = Path(os.environ["RUN_DIR"])
inputs = json.loads((run / "manifest.json").read_text())
missing = []
for index, source in enumerate(inputs):
    target = run / "results" / f"{index:06d}.json"
    if not target.exists():
        missing.append(source)
        continue
    result = json.loads(target.read_text())
    if result["input"] != source or "axes" not in result or "object" not in result:
        raise RuntimeError(f"Invalid result: {target}")
(run / "missing.json").write_text(json.dumps(missing, indent=2))
print(f"Verified {len(inputs) - len(missing)} of {len(inputs)} outputs")
print(f"Missing inputs: {len(missing)}")
```

Inspect errors and fix the cause before retrying. Wait until the previous
attempt's Sessions have stopped, or cancel them explicitly and confirm they
are gone. Do not run recovery concurrently against the same output directory.

Keep the original manifest unchanged. With a new attempt name, resubmit the
same run; the worker skips verified existing outputs and processes the missing
ones. For example, after validating one-worker behavior:

```bash title="Terminal inside your controller Session"
python submit.py attempt-002 2
python verify_outputs.py
```

Malformed output fails visibly instead of being silently replaced. Preserve it
for diagnosis, then remove only the affected output after checking the input.
Output existence is only this example's completion check; a scientific
reduction should also verify its own quality and provenance requirements.

<span id="cleanup-a-batch"></span>

## 5. Save results and clean up

All manifests, outputs, and diagnostics in this example are already under
persistent `/arc` storage. Record the worker's code revision with the run and
verify that another Session can read the results before deleting compute.

The following script asks you to name one attempt and deletes only its recorded
Session IDs. Run it with `python cleanup.py attempt-001`:

```python title="cleanup.py"
import json
import os
import sys
from pathlib import Path

from canfar.sessions import Session

run = Path(os.environ["RUN_DIR"])
attempt = json.loads((run / f"{sys.argv[1]}.json").read_text())
with Session() as session:
    print(session.destroy(attempt["ids"]))
```

Each ID maps to a deletion-request result. Investigate `False` results before
assuming cleanup succeeded. Keep run records and outputs for reproducibility;
do not use a broad name-prefix cleanup for unrelated Sessions.

## Related guides

- [Common examples](examples.md) for matching sync/async operations.
- [Distributed helpers](helpers.md) for partitioning behavior and validation.
- [Data access](data.md) for staging and caching remote inputs.
- [Container Images](../platform/containers/index.md) for software environments.
