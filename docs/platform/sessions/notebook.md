# Notebook Sessions

A Notebook Session provides a browser-based Jupyter environment for interactive
analysis. It is a good place to explore data, test a reduction, and prepare a
command for a [headless Session](batch.md).

## Launch a Notebook

1. Sign in to the [Science Portal](https://www.canfar.net/science-portal/).
2. Under **Launch New Session**, choose **Notebook** and an image that contains
   your analysis software. Complete the resource choices offered by the form
   and launch the Session.
3. Find the new entry under **Active Sessions**. Wait for it to start, then
   open its notebook link to enter Jupyter.

Available packages, graphics processors (GPUs), and resource limits depend on
the selected image and server. If the Session does not start, check its status
in the portal and consult [Support](../support/index.md).

## Create, run, and save a notebook

1. In Jupyter's file browser, navigate to `/arc/home/USER`, replacing `USER`
   with your CADC username. You can use `/arc/projects/PROJECT` instead if
   your project has given you write access.
2. Open a launcher and choose a Python notebook, or use **New** and select a
   Python kernel if your image provides the classic notebook interface.
3. Enter the following code in the first cell, then press **Shift+Enter**:

    ```python
    print("Ready to analyse your data")
    ```

4. Confirm that the message appears below the cell. Rename the notebook to
   `first-analysis.ipynb` and use **File → Save Notebook** (or **Save and
   Checkpoint** in the classic interface).
5. Confirm that the saved file appears under your chosen `/arc` directory.
   Use [Storage Management](../storage/transfers.md#transfer-files-in-your-browser)
   to upload inputs or download a copy of the notebook.

Save your results before you finish. Return to **Active Sessions** in the
Science Portal, use the delete control for this Session, and confirm the
deletion. Files saved under `/arc` remain; `/scratch` and unsaved kernel state
do not. Closing Jupyter's browser tab does not delete the Session.

## Launch from the command line (optional)

After [installing the client](../../client/get-started.md#install), list the images available on the active server before choosing one:

```bash
canfar login cadc
canfar image ls --kind notebook
canfar create notebook IMAGE_NAME --name analysis
```

Use `canfar create --help` to check the resource options supported by your
installed client.

Monitor the Session and open it when it is ready:

```bash
canfar ps --all
canfar info SESSION_ID
canfar open SESSION_ID
```

If it remains `Pending`, inspect `canfar events SESSION_ID` and the
[batch troubleshooting guide](batch.md#monitor-and-troubleshoot). A Session
that is not ready has no application logs yet; use `canfar logs` after it has
started.

## Work with files

Use the mounted paths supplied by your server:

```text
/arc/home/<user>/          personal persistent files
/arc/projects/<project>/   project files, when available
/scratch/                  temporary Session-local staging
```

Save notebooks, code, and results under `/arc` or a persistent VOSpace
Service. `/scratch` is useful for high-I/O intermediates and is deleted when
the Session ends. For remote data that is not mounted, use [CANFAR data
transfers](../storage/transfers.md) or the [Python filesystem
helpers](../storage/filesystem.md).

The Jupyter file browser and terminal operate inside the Session. Large local
uploads are often more reliable when copied explicitly with `canfar data cp`.

## Use a specialised image

If a published image includes CASA or another astronomy package, follow that
image's documentation. Do not assume that every Notebook has the same Python
packages or that installing a package in one Session changes another. For
repeatable work, pin dependencies in a Container Image or versioned
environment.

Some deployments also expose shared software through [CVMFS](../cvmfs.md).
Treat it as read-only and record the module and version used by a workflow.

## Move from exploration to automation

Keep the notebook for inspection and use a script with explicit input/output
paths for repeatable reductions:

```python
from pathlib import Path

input_path = Path("/arc/projects/<project>/input.fits")
output_path = Path("/arc/projects/<project>/results/output.fits")
# Load input_path, run the reduction, and write output_path.
```

Then submit the same command as a headless Session, following the
[batch guide](batch.md). Record the image, resource request, Storage
Identifiers, and code revision with the run.

## Troubleshooting

- A kernel that will not start may indicate an image or resource problem;
  inspect `info`, `events`, and the Session resource request.
- A missing file is usually a path, identifier, or group-permission issue;
  confirm it with `canfar data info IDENTIFIER:/path`.
- A slow notebook may be reading a remote object repeatedly. Stage it once to
  `/scratch` or use the opt-in cache guidance in [Filesystem and Python
  tools](../storage/filesystem.md).
- A lost browser connection does not necessarily mean the Session stopped;
  check `canfar ps --all` first.

See [Support](../support/index.md) when the checks do not identify the cause.
