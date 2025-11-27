# From Interactive Notebooks to Batch Processing with CANFAR

!!! tip "Who is this for?"
    This presentation is for astronomers who want to:

    - **Run code on the cloud** without complex setup.
    - Use familiar tools like **Jupyter Notebooks**.
    - Scale their analysis from a single interactive session to **hundreds of parallel jobs**.
    - **Process large datasets** efficiently.

    **Whether you're new to coding or a seasoned power-user, these tools are designed to be intuitive and powerful.**

## CLI: Your Mission Control

The `canfar` CLI is the easiest way to get started. It's your interactive mission control for the CANFAR science platform.

### Step 0: Prerequisites

Install `pipx` if you don't have it already. `pipx` is a tool for installing and running Python applications in isolated environments.

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Alternatively, on you can use OS specific package managers:

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

It's a single command. Open your terminal and type:

```bash
pipx install canfar
```

??? info "Installation Walkthrough"
    <script src="https://asciinema.org/a/IVLebHvaeWcBrPqlBa3hD2swz.js" id="asciicast-IVLebHvaeWcBrPqlBa3hD2swz" async="true"></script> #pragma: allowlist secret

### Step 2: First Contact (Authentication)

Tell `canfar` who you are. This command discovers all available servers worldwide and guides you through a one-time login.

```bash
canfar auth login -f
```

??? info "Auth Walkthrough"
    <script src="https://asciinema.org/a/a0bGaulLPlR2g3Go95I5BYKIz.js" id="asciicast-a0bGaulLPlR2g3Go95I5BYKIz" async="true"></script> #pragma: allowlist secret

You'll be prompted for your credentials, and the CLI handles the rest, saving a secure token for future commands.

!!! success "What just happened?"

    - We installed the `canfar` python package, which provides the `canfar` command-line interface (CLI).
    - We authenticated with the CANFAR Science Platform.
    - All future commands will use this secure authentication context automatically.

---

## Your First Interactive Notebook

Let's launch a Jupyter notebook that comes pre-loaded with common astronomy libraries like `AstroPy`, `SciPy`, and `Matplotlib`.

### Step 1: Create the Notebook

```bash
# Launch a notebook using a pre-built astronomy image
canfar create notebook skaha/astroml:latest
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

Use the session ID to open the notebook directly in your web browser.

```bash
canfar open <SESSION_ID>
```

!!! success "You're in!"
    You now have a fully functional JupyterLab environment running on the powerful CANFAR Science Platform. 

### Step 4: Clean Up

When you're finished, it's important to delete your session to free up resources for others.

```bash
canfar delete <SESSION_ID>
```

??? "Clean Up Walkthrough"
    <script src="https://asciinema.org/a/eQHnbK2Y5qnVogwELX1UUpUf3.js" id="asciicast-eQHnbK2Y5qnVogwELX1UUpUf3" async="true"></script> #pragma: allowlist secret

---

## The Power of Headless Mode: From Interactive to Batch

This is where the magic happens.

What if you have a Python script that runs your analysis, and you don't need the full interactive notebook? You can run it in **"headless" (batch) mode** using the *exact same container image*.

Let's say you have a script named `echo.py`.

```bash
canfar create headless skaha/astroml:latest -- python echo.py
```

!!! tip "Interactive to Batch, Seamlessly"
    You can develop your analysis interactively in a **notebook** session, save your code to a python script, and then run it at scale using a **headless** session. **No changes to your environment are needed.**

To check the output of your headless job, you can use the `logs` command.

```bash
canfar logs <SESSION_ID>
```

---

## Scaling Up: From One to Many

Need to process hundreds of files? You can launch multiple copies (replicas) of your headless job with a single command.

```bash
canfar create --replicas 10 headless skaha/astroml:latest -- python echo.py
```

You now have 10 containers in parallel. But how do you divide the work?

---

## The Python Client: Distributing Your Workload

For complex logic like distributing data across many jobs, we switch to the `canfar` Python Client.

### The Problem

You have 1000 FITS files and 100 replicas. How does each replica know which files to process?

### The Solution

The `canfar.helpers.distributed` module provides simple but powerful functions to automatically split up a list of files among your replicas.

```python title="Distributing Workloads"
from canfar.helpers import distributed
from glob import glob
# Assume your analysis logic is in this function
from your_code import run_analysis 

# 1. Get a list of all your data files
all_files = glob("/arc/projects/your_project/*.fits")

# 2. 'chunk' automatically gives each replica its unique subset of files
#    It reads environment variables ($REPLICA_ID, $REPLICA_COUNT) set by CANFAR.
my_files = distributed.chunk(all_files)

# 3. Process only your assigned files
print(f"This replica will process {len(list(my_files))} files.")
for datafile in my_files:
    run_analysis(datafile)

print("Done!")
```

!!! info "Work Distribution Strategies"
    - `distributed.chunk(items)`: Divides data into contiguous blocks. Good for files of similar size.
    - `distributed.stripe(items)`: Distributes data like dealing cards (round-robin). Good for files of varying sizes to balance the load.

---

## Putting It All Together: A Complete Workflow

Here is the complete workflow, from launching jobs programmatically to processing data in parallel.

```python title="Launching Jobs Programmatically"
from canfar.sessions import Session

# This uses the same authentication from 'canfar auth login'
session = Session()

# Launch 100 replicas, each running our processing script
ids = session.create(
    name="galaxy-processing-batch",
    kind="headless",
    image="skaha/astroml:latest",
    cmd="python",
    args=["my_script.py"],
    replicas=100,
)

print(f"Successfully launched {len(ids)} processing jobs!")
```