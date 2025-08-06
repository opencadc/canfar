# Advanced Examples

Complex use cases and power-user examples for Skaha and the CANFAR Science Platform.

# Quick Start

!!! info
    Skaha automatically sets these environment variables in each container:

    - `REPLICA_ID`: Current container ID (1, 2, 3, ...)
    - `REPLICA_COUNT`: Total number of containers

## Massively Parallel Processing

Let's assume you have a large dataset of 1000 FITS files that you want to process in parallel. You have a Python script that can process a single FITS file, and you want to run this script in parallel on 100 different Skaha sessions.

```python title="batch_processing.py"
from skaha.helpers import distributed
from glob import glob
from your.code import process_datafile

# Find all FITS files to process
datafiles = glob("/path/to/data/files/*.fits")

# Each replica processes its assigned chunk of files
# The chunk function automatically handles 1-based REPLICA_ID values
for datafile in distributed.chunk(datafiles):
    process_datafile(datafile)
```

### Launching Analysis with Python API

```python title="Large-Scale Parallel Processing"
from skaha.session import AsyncSession

async with AsyncSession() as session:
    sessions = await session.create(
        name="fits-processing",
        image="images.canfar.net/your/analysis-container:latest",
        kind="headless",
        cores=8,
        ram=32,
        cmd="python",
        args=["/path/to/batch_processing.py"],
        replicas=100,
    )
    return sessions
```

### Launching Analysis with CLI

```bash title="Large-Scale Parallel Processing"
skaha create -c 8 -m 32 -r 100 -n fits-processing headless images.canfar.net/your/analysis-container:latest -- python /path/to/batch_processing.py
```

## Distributed Processing Strategies

Skaha provides two main strategies for distributing data across replicas:

### Chunking Strategy (`distributed.chunk`)

The `chunk` function divides your data into contiguous blocks, with each replica processing a consecutive chunk. The function uses 1-based replica IDs (matching Skaha's `REPLICA_ID` environment variable):

```python title="Chunking Example"
from skaha.helpers import distributed

# With 1000 files and 100 replicas:
# - Replica 1 processes files 0-9
# - Replica 2 processes files 10-19  
# - Replica 3 processes files 20-29
# - And so on...

datafiles = glob("/path/to/data/*.fits")
for datafile in distributed.chunk(datafiles):
    process_datafile(datafile)
```

### Striping Strategy (`distributed.stripe`)

The `stripe` function distributes data in a round-robin fashion, which is useful when file sizes vary significantly:

```python title="Striping Example"
from skaha.helpers import distributed

# With 1000 files and 100 replicas:
# - Replica 1 processes files 0, 100, 200, 300, ...
# - Replica 2 processes files 1, 101, 201, 301, ...
# - Replica 3 processes files 2, 102, 202, 302, ...
# - And so on...

datafiles = glob("/path/to/data/*.fits")
for datafile in distributed.stripe(datafiles):
    process_datafile(datafile)
```

### When to Use Each Strategy

- **Use `chunk`** when files are similar in size and you want each replica to process a contiguous block of data
- **Use `stripe`** when file sizes vary significantly, as it distributes the workload more evenly across replicas

## Real-World Example: Processing Astronomical Data

```python
import os
import json
from pathlib import Path
from skaha.helpers.distributed import chunk

def process_observations():
    """Process FITS files across multiple containers."""

    # Get all observation files
    fits_files = list(Path("/data/observations").glob("*.fits"))
    my_files = list(chunk(fits_files))

    if not my_files:
        print("No files assigned to this container")
        return

    replica_id = os.environ.get('REPLICA_ID')
    print(f"Container {replica_id} processing {len(my_files)} files")

    # Process each file
    results = []
    for fits_file in my_files:
        # Your analysis code here
        result = {"file": fits_file.name, "stars_detected": analyze_fits(fits_file)}
        results.append(result)

    # Save results with container ID
    output_file = f"/results/container_{replica_id}_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} results to {output_file}")

def analyze_fits(fits_path):
    """Your FITS analysis logic here."""
    return 42  # Placeholder
```

## Best Practices

**Choose the right function:**
- Use `chunk()` when you need contiguous data blocks
- Use `stripe()` for round-robin distribution

**Handle empty containers:**
```python
my_data = list(chunk(data))
if not my_data:
    print("No data for this container")
    return
```

**Save results with container ID:**
```python
import os
replica_id = os.environ.get('REPLICA_ID')
output_file = f"/results/container_{replica_id}_results.json"
```

**Combine results from all containers:**
```python
from pathlib import Path
import json

def combine_results():
    """Merge results from all containers."""
    all_results = []
    for result_file in Path("/results").glob("container_*_results.json"):
        with open(result_file) as f:
            all_results.extend(json.load(f))

    with open("/results/final_results.json", 'w') as f:
        json.dump(all_results, f, indent=2)
```

## Creating Distributed Sessions

Create multiple containers for distributed processing:

```bash
# Create 5 containers for distributed analysis
skaha create headless images.canfar.net/skaha/astronomy:latest -r 5 -- python3 /scripts/process_data.py
```

## Common Issues

**Some containers get no data**
This happens when you have more containers than data items. Handle it gracefully:
```python
my_data = list(chunk(data))
if not my_data:
    print("No data assigned to this container")
    return
```

**Debugging distribution**
```python
import os
replica_id = os.environ.get('REPLICA_ID')
replica_count = os.environ.get('REPLICA_COUNT')
print(f"Container {replica_id} of {replica_count} processing {len(my_data)} items")
```

