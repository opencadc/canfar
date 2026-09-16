# From Interactive Notebooks to Batch Processing with CANFAR

!!! tip "Who is this for?"
    This presentation is for astronomers who want to:

    - **Run code on the cloud** without complex setup.
    - Use familiar tools like **Jupyter Notebooks**.
    - Scale their analysis from a single interactive Session to **hundreds of parallel Sessions**.
    - **Process large datasets** efficiently.

    Start with one small analysis, then add replicas after you verify the results.

## CLI: Your Mission Control

Use the `canfar` command-line interface (CLI) for this workshop. If you prefer
to start in your browser, follow [Getting Started](../platform/get-started.md);
you do not need to install the client for that route.

### Step 0: Prerequisites

Install `pipx` if you don't have it already. `pipx` is a tool for installing and running Python applications in isolated environments.

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Alternatively, use your operating system’s package manager:

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

    These examples describe the unreleased interface on this branch.
    `pipx install canfar` installs the published release, which may differ.
    Follow [installation and capability checks](../client/get-started.md#try-this-development-branch)
    before continuing. Older recordings may also show earlier commands.

For a published release, open your terminal and type:

```bash
pipx install canfar
```

??? info "Installation Walkthrough"
    <script src="https://asciinema.org/a/IVLebHvaeWcBrPqlBa3hD2swz.js" id="asciicast-IVLebHvaeWcBrPqlBa3hD2swz" async="true"></script> #pragma: allowlist secret

### Step 2: First Contact (Authentication)

Tell `canfar` who you are. This command discovers the servers available to the
selected identity and guides you through a one-time login.

```bash
canfar login srcnet -f
```

??? info "Auth Walkthrough"
    <script src="https://asciinema.org/a/a0bGaulLPlR2g3Go95I5BYKIz.js" id="asciicast-a0bGaulLPlR2g3Go95I5BYKIz" async="true"></script> #pragma: allowlist secret

You'll be prompted for your credentials, and the CLI handles the rest, saving
an Authentication Record for future commands.

!!! success "What just happened?"

    - We installed the `canfar` python package, which provides the `canfar` command-line interface (CLI).
    - We authenticated with the CANFAR Science Platform.
    - Future commands use the selected Authentication Record and Server.

---

## Your First Interactive Notebook

Let's launch a Jupyter notebook that comes pre-loaded with common astronomy libraries like `AstroPy`, `SciPy`, and `Matplotlib`.

### Step 1: Create the Notebook

```bash
# See the images available on this server, then launch one
canfar image ls --kind notebook
canfar create notebook IMAGE_NAME
```

??? "Create Notebook Walkthrough"
    <script src="https://asciinema.org/a/RXcq9uqXnx31TFM420pJdoId4.js" id="asciicast-RXcq9uqXnx31TFM420pJdoId4" async="true"></script> #pragma: allowlist secret

The CLI will return a unique `SESSION_ID` for your notebook (e.g., `d1tsqexh`).

### Step 2: Check the Status of Your Session

```bash
canfar ps --all
```

??? "Check Status Walkthrough"
    <script src="https://asciinema.org/a/IXgNpwRGNratcRFnqOKXRh3qA.js" id="asciicast-IXgNpwRGNratcRFnqOKXRh3qA" async="true"></script> #pragma: allowlist secret

### Step 3: Open in Your Browser

Wait for your Session to become ready. Replace `SESSION_ID` with its returned
ID to open it in your browser.

```bash
canfar open SESSION_ID
```

!!! success "You're in!"
    You now have a fully functional JupyterLab environment running on the powerful CANFAR Science Platform. 

### Step 4: Clean Up

!!! warning "Save your work before deleting compute"

    Save notebooks, scripts, and results under persistent `/arc` storage. Verify
    that a new Session can read them before deleting the old Session.

Delete only the Session you created to free resources for others:

```bash
canfar delete SESSION_ID
```

??? "Clean Up Walkthrough"
    <script src="https://asciinema.org/a/eQHnbK2Y5qnVogwELX1UUpUf3.js" id="asciicast-eQHnbK2Y5qnVogwELX1UUpUf3" async="true"></script> #pragma: allowlist secret

---

## The Power of Headless Mode: From Interactive to Batch

What if you have a Python script that runs your analysis, and you don't need the full interactive notebook? You can run it in **"headless" (batch) mode** using the *exact same container image*.

Save your tested script at `/arc/projects/PROJECT/echo.py`. Replace `PROJECT`
and `IMAGE_NAME` below; the image must contain Python and your dependencies.
The headless Session must have permission to read the script and inputs.

```bash
canfar create headless IMAGE_NAME -- python /arc/projects/PROJECT/echo.py
```

!!! tip "Interactive to Batch, Seamlessly"
    You can develop your analysis interactively in a **notebook** session, save your code to a python script, and then run it at scale using a **headless** session. **No changes to your environment are needed.**

To check the output of your headless Session, you can use the `logs` command.

```bash
canfar logs SESSION_ID
```

---

## Scaling Up: From One to Many

Need to process hundreds of files? You can launch multiple copies (replicas) of your headless Session with a single command.

```bash
canfar create --replicas 2 headless IMAGE_NAME -- python /arc/projects/PROJECT/echo.py
```

This requests two Sessions; admission and capacity determine when they run.
Keep the accepted IDs and check their status and outputs. A partial submission
can leave some inputs unprocessed.

---

## The Python Client: Distributing Your Workload

For complex logic like distributing data across many Sessions, we switch to the `canfar` Python Client.

### The Problem

You have several Flexible Image Transport System (FITS) files and two replicas.
Each replica needs the same ordered input list to choose its own share.

### The Solution

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

!!! info "Work Distribution Strategies"
    - `distributed.chunk(items)`: Divides data into contiguous blocks. Good for files of similar size.
    - `distributed.stripe(items)`: Distributes data like dealing cards (round-robin). Good for files of varying sizes to balance the load.

---

## Putting It All Together: A Complete Workflow

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
