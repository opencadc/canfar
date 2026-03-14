# Python Client Examples

These examples use the asynchronous API for best performance and scalability.

!!! note "Assumption"
      ```bash title="Authenticated via CLI"
      canfar auth login
      ```

## Create Sessions

### Notebook

=== "Flexible Mode (Default)"

    ```python
    from canfar.sessions import Session

    session = Session()
    ids = session.create(
        name="my-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
    )
    print(ids)  # ["d1tsqexh"]
    session.connect(ids)
    ```

=== "Fixed Mode"

    ```python
    from canfar.sessions import Session

    session = Session()
    ids = session.create(
        name="my-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
        cores=2,
        ram=4,
    )
    print(ids)  # ["d1tsqexh"]
    session.connect(ids)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    session = AsyncSession()
    ids = await session.create(
        name="my-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
    )
    print(ids)  # ["d1tsqexh"]
    await session.connect(ids)
    ```

### Headless

- Headless sessions are are containers that execute a command and exit when complete without user interaction.
- They are useful for batch processing and distributed computing.


=== "Replicated Headless Sessions"

    ```python
    from canfar.sessions import Session

    session = Session()
    ids = session.create(
        name="my-headless",
        image="images.canfar.net/skaha/astroml:latest",
        kind="headless",
        cmd="echo",
        args=["Hello, World!"],
    )
    print(ids)  # ["d1tsqexh"]
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    session = AsyncSession()
    ids = await session.create(
        name="my-headless",
        image="images.canfar.net/skaha/astroml:latest",
        kind="headless",
        cmd="echo",
        args=["Hello, World!"],
    )
    print(ids)  # ["d1tsqexh"]
    ```


!!! example "Replica Environment Variables"
    All containers receive the following environment variables:
    - `REPLICA_COUNT` — common total number of replicas
    - `REPLICA_ID` — 1-based index of the replica (1..N)

    Use these to partition work deterministically. See [Helpers API Reference](helpers.md) for `chunk` and `stripe`.

!!! warning "Private Container Registry Access"
    Use a private Harbor image by providing registry credentials via configuration.
    ```python
    import asyncio
    from canfar.sessions import AsyncSession
    from canfar.models.registry import ContainerRegistry
    from canfar.models.config import Configuration

    async def main():
        cfg = Configuration(registry=ContainerRegistry(username="username", secret="CLI_SECRET"))
        session = AsyncSession(config=cfg)
        ids = await session.create(
            name="private-job",
            image="images.canfar.net/your/private-image:latest",
            kind="headless",
            cmd="python",
            args=["/app/run.py"],
        )
        print(ids)

    asyncio.run(main())
    ```

## Resource Allocation Modes

CANFAR supports two resource allocation modes for your sessions. See the [resource allocation guide](../platform/concepts.md#resource-allocation-modes) for more information.

### Examples

=== "Flexible Mode (Default)"
    ```python
    from canfar.sessions import Session

    session = Session()
    # No cores/ram specification - uses flexible allocation
    ids = session.create(
        name="flexible-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook"
    )
    ```

=== "Fixed Mode"
    ```python
    from canfar.sessions import Session

    session = Session()
    # Specify exact resources for guaranteed allocation
    ids = session.create(
        name="fixed-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
        cores=4,
        ram=8
    )
    ```

## Discover and Filter Sessions

=== "Fetch All Sessions"

    ```python
    from canfar.sessions import Session

    session = Session()
    all_sessions = session.fetch()
    print(len(all_sessions))
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    with AsyncSession() as session:
        all_sessions = await session.fetch()
        print(len(all_sessions))
    ```
<br>

=== "Fetch Running Notebooks"

    ```python
    from canfar.sessions import Session

    session = Session()
    running = session.fetch(kind="notebook", status="Running")
    print(running)
    session.connect(running)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        running = await session.fetch(kind="notebook", status="Running")
        print(running)
        await session.connect(running)
    ```
<br>

=== "Fetch Completed Headless Sessions"

    ```python
    from canfar.sessions import Session

    session = Session()
    completed = session.fetch(kind="headless", status="Succeeded")
    print(completed)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        completed = await session.fetch(kind="headless", status="Succeeded")
        print(completed)
    ```

!!! success "Kinds & Status"

    You can use any combination of the following kinds and status to filter sessions:

    - Kinds: `desktop`, `notebook`, `carta`, `headless`, `firefly`, `desktop-app`, `contributed`
    - Statuses: `Pending`, `Running`, `Terminating`, `Succeeded`, `Error`, `Failed`


## Inspect Sessions

Detailed information about the session, including resource usage, user IDs, and more.

=== "Detailed Session Information"

    ```python
    from canfar.sessions import Session

    session = Session()
    info = session.info(ids)
    print(info)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        info = await session.info(ids)
        print(info)
    ```

## Events

Events describe the steps taken by the Science Platform to launch your session

=== "Session Events"

    ```python
    from canfar.sessions import Session

    session = Session()
    events = session.events(ids, verbose=True)
    print(events)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        events = await session.events(ids, verbose=True)
        print(events)
    ```

## Logs

Logs contain the output from your session's containers. 

!!! tip "Log Retention"
    Logs are retained until your session is deleted. A completed session, i.e., `Succeeded`, `Failed`, or `Error` is kept for 24 hours before being deleted.

=== "Session Logs"

    ```python
    from canfar.sessions import Session

    session = Session()
    logs = session.logs(ids, verbose=True)
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        logs = await session.logs(ids, verbose=True)
    ```

## Cleanup Sessions

!!! warning "Permanent Action"

    Deleted sessions cannot be recovered.

=== "Destroy Session(s)"

    ```python
    from canfar.sessions import Session

    session = Session()
    result = session.destroy(ids)
    print(result)  # {"id": True, ...}
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        result = await session.destroy(ids)
        print(result)  # {"id": True, ...}
    ```
<br>
=== "Bulk Destroy"

    ```python
    from canfar.sessions import Session

    session = Session()
    result = session.destroy_with(prefix="test-", kind="headless", status="Succeeded")
    print(result)  # {"id": True, ...}
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    async with AsyncSession() as session:
        result = await session.destroy_with(prefix="test-", kind="headless", status="Succeeded")
        print(result)  # {"id": True, ...}
    ```

## VOSpace File Management

The `VOSpaceClient` provides programmatic access to VOSpace storage using your CANFAR authentication.

### Basic Operations

=== "List Directory"

    ```python
    from canfar.vospace import VOSpaceClient

    vospace = VOSpaceClient()
    client = vospace.vos_client

    # List root directory
    files = client.listdir("vos:")
    for f in files:
        print(f)
    ```

=== "Upload Files"

    ```python
    from canfar.vospace import VOSpaceClient

    vospace = VOSpaceClient()
    client = vospace.vos_client

    # Upload a file
    client.copy("local_data.fits", "vos:/data/remote_data.fits")

    # Upload a directory (recursive)
    client.copy("./local_dir/", "vos:/data/remote_dir/")
    ```

=== "Download Files"

    ```python
    from canfar.vospace import VOSpaceClient

    vospace = VOSpaceClient()
    client = vospace.vos_client

    # Download a file
    client.copy("vos:/data/file.fits", "./local_file.fits")

    # Download multiple files with glob
    for remote in client.glob("vos:/data/*.fits"):
        name = remote.split("/")[-1]
        client.copy(remote, f"./{name}")
    ```

### Directory Management

=== "Create Directory"

    ```python
    from canfar.vospace import VOSpaceClient

    vospace = VOSpaceClient()
    client = vospace.vos_client

    # Create a directory
    client.mkdir("vos:/data/new_project")

    # Check if exists first
    if not client.access("vos:/data/new_project"):
        client.mkdir("vos:/data/new_project")
    ```

=== "Delete Files"

    ```python
    from canfar.vospace import VOSpaceClient

    vospace = VOSpaceClient()
    client = vospace.vos_client

    # Delete a file
    client.delete("vos:/data/old_file.fits")

    # Delete directory recursively
    successes, failures = client.recursive_delete("vos:/data/old_dir/")
    print(f"Deleted {successes}, failed {failures}")
    ```

=== "Move/Rename"

    ```python
    from canfar.vospace import VOSpaceClient

    vospace = VOSpaceClient()
    client = vospace.vos_client

    # Rename a file
    client.move("vos:/data/old.fits", "vos:/data/new.fits")

    # Move to another directory
    client.move("vos:/data/file.fits", "vos:/archive/file.fits")
    ```

### Node Information & Properties

=== "Get Node Info"

    ```python
    from canfar.vospace import VOSpaceClient

    vospace = VOSpaceClient()
    client = vospace.vos_client

    # Get node details
    node = client.get_node("vos:/data/file.fits")
    info = node.get_info()

    print(f"Size: {info['size']} bytes")
    print(f"Permissions: {info['permissions']}")
    print(f"Owner: {info['creator']}")
    print(f"Is locked: {node.is_locked}")
    ```

=== "Set Properties"

    ```python
    from canfar.vospace import VOSpaceClient

    vospace = VOSpaceClient()
    client = vospace.vos_client

    # Get node and set custom property
    node = client.get_node("vos:/data/file.fits", force=True)
    node.props["quality"] = "verified"
    node.props["processing_date"] = "2026-01-14"
    client.update(node)

    # Read properties
    print(node.props)
    ```

=== "Manage Permissions"

    ```python
    from canfar.vospace import VOSpaceClient

    vospace = VOSpaceClient()
    client = vospace.vos_client

    node = client.get_node("vos:/data/file.fits")

    # Make public
    client.update(node, {"ispublic": "true"})

    # Add group read permission
    client.update(node, {"readgroup": "ivo://cadc.nrc.ca/gms#MyGroup"})

    # Make private again
    client.update(node, {"ispublic": "false"})
    ```

### Combined Session + VOSpace Workflow

A typical data processing workflow using both Sessions and VOSpace:

```python
from canfar.vospace import VOSpaceClient
from canfar.sessions import Session
import time

# Initialize clients
vospace = VOSpaceClient()
vos = vospace.vos_client
session = Session()

# 1. Create project directory
if not vos.access("vos:/arc/home/user/analysis"):
    vos.mkdir("vos:/arc/home/user/analysis")

# 2. Upload input data
print("Uploading input data...")
vos.copy("./observations/", "vos:/arc/home/user/analysis/input/")

# 3. Upload processing script
vos.copy("./process_data.py", "vos:/arc/home/user/analysis/process_data.py")

# 4. Launch headless processing session
print("Starting processing session...")
ids = session.create(
    name="data-analysis",
    image="images.canfar.net/skaha/astroml:latest",
    kind="headless",
    cmd="python",
    args=["/arc/home/user/analysis/process_data.py"],
    cores=4,
    ram=16
)
print(f"Session started: {ids[0]}")

# 5. Monitor progress
while True:
    info = session.fetch()
    current = next((s for s in info if s.id == ids[0]), None)
    if current:
        print(f"Status: {current.status}")
        if current.status in ["Succeeded", "Failed", "Error"]:
            break
    time.sleep(30)

# 6. Download results
print("Downloading results...")
for result_file in vos.glob("vos:/arc/home/user/analysis/output/*.fits"):
    local_name = result_file.split("/")[-1]
    vos.copy(result_file, f"./results/{local_name}")
    print(f"Downloaded: {local_name}")

# 7. Clean up session
session.destroy(ids)
print("Done!")
```

!!! tip "VOSpace Paths in Sessions"
    Files in VOSpace are automatically mounted in sessions:

    - `vos:/arc/home/username/` → `/arc/home/username/`
    - `vos:/arc/projects/myproject/` → `/arc/projects/myproject/`

    You can read and write directly to these paths from within your session.
