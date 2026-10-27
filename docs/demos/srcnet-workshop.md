# From interactive notebooks to batch processing with CANFAR

!!! tip "Who is this for?"
    This workshop is for astronomers who want to:

    - Run analysis code on CANFAR without setting up a remote machine.
    - Work in Jupyter notebooks.
    - Scale an analysis from one interactive Session to many parallel Sessions.
    - Process multi-file datasets with replicas.

    Start with one small analysis, then add replicas after you verify the results.

## CLI setup

Use the `canfar` command-line interface (CLI) for this workshop. If you prefer
to start in your browser, follow [Getting Started](../platform/get-started.md);
you do not need to install the client for that route.

### Step 0: Prerequisites

Install `pipx` if you don't have it already. `pipx` installs and runs Python applications in isolated environments.

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Alternatively, use your operating system's package manager:

=== "macOS"

    ```bash
    brew install pipx
    pipx ensurepath
    ```

=== "Linux (Ubuntu/Debian)"

    ```bash
    sudo apt update
    sudo apt install pipx
    pipx ensurepath
    ```

=== "Windows (scoop)"

    ```powershell
    scoop install pipx
    pipx ensurepath
    ```


### Step 1: Installation

!!! warning "Check your client version first"

    These examples use the released v1.5.2 client. Follow the
    [installation guide](../client/get-started.md#install) before continuing.
    Older recordings may show earlier commands; use the text examples and
    installed command help for the current syntax.

For a published release, open your terminal and type:

```bash
pipx install canfar
```

??? info "Installation walkthrough"
    <script src="https://asciinema.org/a/IVLebHvaeWcBrPqlBa3hD2swz.js" id="asciicast-IVLebHvaeWcBrPqlBa3hD2swz" async="true"></script> #pragma: allowlist secret

### Step 2: Authentication

Log in to your identity provider. This command discovers the servers available
to the selected identity and guides you through a login.

```bash
canfar login srcnet -f
```

??? info "Auth walkthrough"
    <script src="https://asciinema.org/a/a0bGaulLPlR2g3Go95I5BYKIz.js" id="asciicast-a0bGaulLPlR2g3Go95I5BYKIz" async="true"></script> #pragma: allowlist secret

The CLI prompts for your credentials and saves an Authentication Record and
Server Selection for future commands.

!!! success "What just happened?"

    - You installed the `canfar` Python package, which provides the `canfar` CLI.
    - You authenticated with the CANFAR Science Platform.
    - Future commands use the selected Authentication Record and Server.

---

## Your first interactive notebook

Launch a Jupyter notebook image that includes astronomy libraries such as `astropy`, `scipy`, and `matplotlib`.

### Step 1: Create the notebook

```bash
# See the images available on this server, then launch one
canfar image ls --kind notebook
canfar create notebook IMAGE_NAME
```

??? "Create notebook walkthrough"
    <script src="https://asciinema.org/a/RXcq9uqXnx31TFM420pJdoId4.js" id="asciicast-RXcq9uqXnx31TFM420pJdoId4" async="true"></script> #pragma: allowlist secret

The CLI prints a `SESSION_ID` for your notebook, such as `d1tsqexh`.

### Step 2: Check the status of your Session

```bash
canfar ps --all
```

??? "Check status walkthrough"
    <script src="https://asciinema.org/a/IXgNpwRGNratcRFnqOKXRh3qA.js" id="asciicast-IXgNpwRGNratcRFnqOKXRh3qA" async="true"></script> #pragma: allowlist secret

### Step 3: Open in your browser

Wait for your Session to reach `Running`. Replace `SESSION_ID` with the
returned ID to open it in your browser.

```bash
canfar open SESSION_ID
```

!!! success "Notebook ready"
    Your JupyterLab Session is running on the Science Platform.

### Step 4: Clean up

!!! warning "Save your work before deleting compute"

    Save notebooks, scripts, and results under persistent `/arc` storage. Verify
    that a new Session can read them before deleting the old Session.

Delete only the Session you created to free resources for others:

```bash
canfar delete SESSION_ID
```

??? "Clean up walkthrough"
    <script src="https://asciinema.org/a/eQHnbK2Y5qnVogwELX1UUpUf3.js" id="asciicast-eQHnbK2Y5qnVogwELX1UUpUf3" async="true"></script> #pragma: allowlist secret

---

## Headless mode: from interactive to batch

When your analysis is in a Python script and you do not need an interactive
notebook, run it in a `headless` Session with the same Container Image.

Save your tested script at `/arc/projects/PROJECT/echo.py`. Replace `PROJECT`
and `IMAGE_NAME` below; the image must contain Python and your dependencies.
The headless Session must have permission to read the script and inputs.

```bash
canfar create headless IMAGE_NAME -- python /arc/projects/PROJECT/echo.py
```

!!! tip "Interactive to batch"
    Develop your analysis interactively in a `notebook` Session, save the code
    to a Python script, and run it in a `headless` Session with the same image.

Read the output of your headless Session with `logs`:

```bash
canfar logs SESSION_ID
```

---

## Scaling up: from one to many

To process many files, launch multiple replicas of your headless Session in one
command:

```bash
canfar create --replicas 2 headless IMAGE_NAME -- python /arc/projects/PROJECT/echo.py
```

This requests two Sessions; admission and capacity determine when they run.
Keep the accepted IDs and check their status and outputs. A partial submission
can leave some inputs unprocessed.

---

## The Python client: distributing your workload

To partition inputs across replicas from Python, use the `canfar` Python client.

### The problem

You have several Flexible Image Transport System (FITS) files and two replicas.
Each replica needs the same ordered input list to choose its own share.

### The solution

The `canfar.helpers.distributed` module partitions an ordered list. First save
an immutable `manifest.json` of input paths, as shown in the
[complete pipeline example](../client/advanced-examples.md#1-record-the-inputs-and-run-settings).
Every worker reads that same file. Adapt this worker fragment with your own
`run_analysis` function; it must write a unique persistent output per input.

```python title="Distributing Workloads"
from canfar.helpers import distributed
import json
from pathlib import Path
# Assume your analysis logic is in this function
from your_code import run_analysis 

# 1. Read the same saved input list in every worker
all_files = json.loads(Path("/arc/projects/PROJECT/run/manifest.json").read_text())

# 2. 'chunk' automatically gives each replica its unique subset of files
#    It reads environment variables ($REPLICA_ID, $REPLICA_COUNT) set by CANFAR.
my_files = list(distributed.chunk(all_files))

# 3. Process only your assigned files
print(f"This replica will process {len(my_files)} files.")
for datafile in my_files:
    run_analysis(datafile)

print("Done!")
```

!!! info "Work distribution strategies"
    - `distributed.chunk(items)`: divides items into contiguous slices. Useful when inputs have similar sizes.
    - `distributed.stripe(items)`: assigns every Nth item in round-robin order. Useful when input sizes vary across the list.

---

## Putting it all together: a complete workflow

This submission example starts two workers. Replace the image and script path
with the ones you tested. For monitoring, result checks, recovery, and scoped
cleanup, follow the [complete pipeline](../client/advanced-examples.md).

```python title="Launching Sessions Programmatically"
from canfar.sessions import Session

# This uses the same Authentication from `canfar login`
with Session() as session:
    # Request two replicas, each running the tested worker script
    ids = session.create(
        name="galaxy-processing-batch",
        kind="headless",
        image="IMAGE_NAME",
        cmd="python",
        args="/arc/projects/PROJECT/run/my_script.py",
        replicas=2,
    )

print(f"Accepted {len(ids)} of 2 requested Sessions: {ids}")
if len(ids) != 2:
    print("Check creation errors and missing outputs before retrying.")
```
