# VOSpaceClient

The `VOSpaceClient` class provides programmatic access to VOSpace file storage, automatically using your CANFAR authentication context.

!!! note "Assumption"
    ```bash title="Authenticated via CLI"
    canfar auth login
    ```

## Overview

`VOSpaceClient` extends `HTTPClient` to provide authenticated access to VOSpace. It automatically:

- Loads your active CANFAR authentication context
- Configures the VOSpace webservice endpoint
- Creates an authenticated `vos.Client` instance

## Basic Usage

```python
from canfar.vospace import VOSpaceClient

# Create client (uses active auth context)
vospace = VOSpaceClient()

# Access the underlying vos.Client
client = vospace.vos_client

# List directory contents
files = client.listdir("vos:")
print(files)
```

## Configuration

### Default VOSpace Host

The default VOSpace webservice is `spsrc27.iaa.csic.es`. You can override this by setting the `VOSPACE_WEBSERVICE` environment variable:

```python
import os
os.environ["VOSPACE_WEBSERVICE"] = "your.vospace.server"

from canfar.vospace import VOSpaceClient
vospace = VOSpaceClient()
```

Or set it in your shell before running Python:

```bash
export VOSPACE_WEBSERVICE=your.vospace.server
python your_script.py
```

## Common Operations

### List Directory Contents

```python
from canfar.vospace import VOSpaceClient

vospace = VOSpaceClient()
client = vospace.vos_client

# List root directory
files = client.listdir("vos:")
for f in files:
    print(f)

# Check if path is a directory
if client.isdir("vos:/data"):
    print("It's a directory")
```

### Upload Files

```python
from canfar.vospace import VOSpaceClient

vospace = VOSpaceClient()
client = vospace.vos_client

# Upload a single file
client.copy("local_file.fits", "vos:/data/file.fits")

# Upload with progress (handled automatically)
client.copy("large_file.fits", "vos:/data/large_file.fits")
```

### Download Files

```python
from canfar.vospace import VOSpaceClient

vospace = VOSpaceClient()
client = vospace.vos_client

# Download a single file
client.copy("vos:/data/file.fits", "./local_file.fits")

# Download with wildcard (use glob first)
for remote_file in client.glob("vos:/data/*.fits"):
    local_name = remote_file.split("/")[-1]
    client.copy(remote_file, f"./{local_name}")
```

### Create Directories

```python
from canfar.vospace import VOSpaceClient

vospace = VOSpaceClient()
client = vospace.vos_client

# Create a directory
client.mkdir("vos:/data/new_directory")

# Check if directory exists first
if not client.access("vos:/data/new_directory"):
    client.mkdir("vos:/data/new_directory")
```

### Delete Files

```python
from canfar.vospace import VOSpaceClient

vospace = VOSpaceClient()
client = vospace.vos_client

# Delete a file
client.delete("vos:/data/old_file.fits")

# Delete a directory recursively
successes, failures = client.recursive_delete("vos:/data/old_directory")
print(f"Deleted {successes} nodes, {failures} failures")
```

### Move/Rename Files

```python
from canfar.vospace import VOSpaceClient

vospace = VOSpaceClient()
client = vospace.vos_client

# Rename a file
client.move("vos:/data/old_name.fits", "vos:/data/new_name.fits")

# Move to another directory
client.move("vos:/data/file.fits", "vos:/archive/file.fits")
```

### Get Node Information

```python
from canfar.vospace import VOSpaceClient

vospace = VOSpaceClient()
client = vospace.vos_client

# Get node details
node = client.get_node("vos:/data/file.fits")
print(f"Size: {node.props.get('length')} bytes")
print(f"Type: {node.type}")
print(f"Is locked: {node.is_locked}")

# Get node info as dictionary
info = node.get_info()
print(f"Permissions: {info['permissions']}")
print(f"Owner: {info['creator']}")
```

### Manage Permissions

```python
from canfar.vospace import VOSpaceClient

vospace = VOSpaceClient()
client = vospace.vos_client

# Get node and modify permissions
node = client.get_node("vos:/data/file.fits")

# Make public
client.update(node, {"ispublic": "true"})

# Make private
client.update(node, {"ispublic": "false"})

# Set group read permission
client.update(node, {"readgroup": "ivo://cadc.nrc.ca/gms#MyGroup"})
```

### Work with Properties/Tags

```python
from canfar.vospace import VOSpaceClient

vospace = VOSpaceClient()
client = vospace.vos_client

# Get node
node = client.get_node("vos:/data/file.fits", force=True)

# Read all properties
for key, value in node.props.items():
    print(f"{key}: {value}")

# Set a custom property
node.props["quality"] = "verified"
client.update(node)

# Delete a property (set to None)
node.props["quality"] = None
client.update(node)
```

## Integration with Sessions

A common workflow is to upload data, process it in a session, and download results:

```python
from canfar.vospace import VOSpaceClient
from canfar.sessions import Session

# Initialize clients
vospace = VOSpaceClient()
vos_client = vospace.vos_client
session = Session()

# 1. Upload input data
vos_client.copy("./input_data/", "vos:/arc/home/user/project/input/")

# 2. Create processing session
ids = session.create(
    name="data-processing",
    image="images.canfar.net/skaha/astroml:latest",
    kind="headless",
    cmd="python",
    args=["/arc/home/user/project/process.py"]
)

# 3. Wait for completion (in practice, poll session.fetch())
import time
while True:
    sessions = session.fetch(kind="headless", status="Succeeded")
    if ids[0] in [s.id for s in sessions]:
        break
    time.sleep(30)

# 4. Download results
for result in vos_client.glob("vos:/arc/home/user/project/output/*.fits"):
    local_name = result.split("/")[-1]
    vos_client.copy(result, f"./results/{local_name}")
```

## Error Handling

```python
from canfar.vospace import VOSpaceClient
from cadcutils import exceptions

vospace = VOSpaceClient()
client = vospace.vos_client

try:
    client.copy("vos:/data/file.fits", "./local.fits")
except exceptions.NotFoundException:
    print("File not found in VOSpace")
except exceptions.ForbiddenException:
    print("Permission denied")
except exceptions.UnauthorizedException:
    print("Authentication required - run 'canfar auth login'")
except Exception as e:
    print(f"Error: {e}")
```

## API Reference

::: canfar.vospace.VOSpaceClient
    options:
      show_root_heading: true
      show_source: false
      members:
        - __init__
        - vos_client

## See Also

- [CLI VOSpace Commands](../cli/cli-help.md#file-management-vospace) - Command-line interface for VOSpace
- [VOSpace Platform Guide](../platform/storage/vospace.md) - Concepts and web interface
- [Python Client Examples](examples.md#vospace-file-management) - More usage examples
