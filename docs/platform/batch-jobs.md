# Batch Jobs and Headless Processing

Batch jobs enable automated, non-interactive processing of astronomical data at scale. This section covers headless execution, API access, job scheduling, and workflow automation on the CANFAR Science Platform.


!!! abstract "🎯 What You'll Learn"
    - The difference between headless and interactive containers
    - How to submit jobs via API and Python client
    - Resource planning, queue behaviour, and monitoring
    - Best practices for automation, logging, and data management
    - [Container Development](containers.md)
    - [Storage Optimization](guides/storage/index.md)
    - [Interactive Sessions](guides/interactive-sessions/index.md)
    - [CANFAR Python Client](../client/home.md)
    - [Support & Troubleshooting](help.md)

## What is Batch Processing?

Batch processing refers to the execution of computational tasks without user interaction, typically running in the background to process large datasets or perform repetitive analysis tasks. In the context of the CANFAR Science Platform, batch jobs run as **headless containers** - containerized environments that execute your code without graphical interfaces or interactive terminals.

### Headless vs Interactive Containers

The key difference between headless and interactive containers lies not in the container images themselves, but in how they are executed. The same container image can be launched in either mode depending on your needs.

**Headless containers** execute a user-specified command or script directly. When you submit a headless job, you specify exactly what command should run - whether it's a Python script, a shell command, or any executable available in the container. The container starts, runs your specified command, and terminates when the command completes. For example, submitting a headless job with the `astroml` container might execute `python /arc/projects/myproject/analysis.py` directly.

**Interactive containers** launch predefined interactive services that you can access through your web browser. The same `astroml` container, when launched interactively, would start Jupyter Lab, providing you with a notebook interface for development and exploration. These containers run indefinitely until you manually stop them, allowing for real-time interaction and iterative development.

This distinction makes headless containers ideal for production workflows and automated processing, while interactive containers excel for development, prototyping, and exploratory data analysis.

## Overview

Batch processing is essential for:

- **Large dataset processing**: Handle terabytes of astronomical data
- **Automated pipelines**: Run standardized reduction workflows
- **Parameter studies**: Execute multiple analysis runs with different parameters
- **Resource optimization**: Run during off-peak hours for better performance
- **Reproducible science**: Documented, automated workflows


!!! tip "When to Use Batch Jobs"
    - Use [Interactive Sessions](guides/interactive-sessions/index.md) to develop and test
    - Switch to headless jobs for production-scale runs
    - Schedule jobs during off-peak hours for faster starts
    - For automation, see [CANFAR Python Client](../client/home.md)


---

!!! info "Quick Links"
    - [Container Development](containers.md)
    - [Storage Guide](guides/storage/index.md)
    - [CANFAR Python Client](../client/home.md)
    - [API Reference](https://ws-uv.canfar.net/skaha/v0/capabilities)
    - [Support](help.md)

### 1. API-Based Execution

Execute containers programmatically using the `canfar` command-line client:

```bash
# Ensure you are logged in first
canfar auth login

# Submit a job
canfar create \
  --name "data-reduction-job" \
  --image "images.canfar.net/skaha/astroml:latest" \
  --cores 4 \
  --ram 16 \
  --cmd "python /arc/projects/myproject/scripts/reduce_data.py"
```

### 2. Job Submission Scripts

Create shell scripts for common workflows using the `canfar` client:

```bash
#!/bin/bash
# submit_reduction.sh

# Set job parameters
JOB_NAME="nightly-reduction-$(date +%Y%m%d)"
IMAGE="images.canfar.net/skaha/casa:6.5"
CMD="python /arc/projects/survey/pipelines/reduce_night.py /arc/projects/survey/data/$(date +%Y%m%d)"

# Submit job
canfar create \
  --name "$JOB_NAME" \
  --image "$IMAGE" \
  --cores 8 \
  --ram 32 \
  --cmd "$CMD"
```

Or using the Python `canfar` client:

```python
#!/usr/bin/env python3
# submit_reduction.py - Python client-based submission

from canfar.sessions import Session
from datetime import datetime

# Initialize session manager
session = Session()

# Set job parameters
job_name = f"nightly-reduction-{datetime.now().strftime('%Y%m%d')}"
image = "images.canfar.net/skaha/casa:6.5"
data_path = f"/arc/projects/survey/data/{datetime.now().strftime('%Y%m%d')}"

# Submit job
job_ids = session.create(
    name=job_name,
    image=image,
    cores=8,
    ram=32,
    cmd="python",
    args=["/arc/projects/survey/pipelines/reduce_night.py", data_path]
)

print(f"Submitted job(s): {job_ids}")
```


### 3. Workflow Automation

Use workflow managers like [Prefect](https://www.prefect.io/) or [Snakemake](https://snakemake.readthedocs.io/en/stable/):

```python
# Snakemake example: workflow.smk
rule all:
    input:
        "results/final_catalog.fits"

rule calibrate:
    input:
        "data/raw/{observation}.fits"
    output:
        "data/calibrated/{observation}.fits"
    shell:
        "python scripts/calibrate.py {input} {output}"

rule source_extract:
    input:
        "data/calibrated/{observation}.fits"
    output:
        "catalogs/{observation}_sources.fits"
    shell:
        "python scripts/extract_sources.py {input} {output}"
```

## Job Types and Use Cases

### Data Reduction Pipelines

**Optical/IR Surveys**:
- Bias, dark, and flat field correction
- Astrometric calibration
- Photometric calibration
- Source extraction and cataloging

**Radio Astronomy**:
- Flagging and calibration
- Imaging and deconvolution
- Spectral line analysis
- Polarization processing

### Scientific Analysis

**Large-scale Surveys**:
- Cross-matching catalogs
- Statistical analysis
- Machine learning training
- Population studies

**Time-domain Astronomy**:
- Light curve analysis
- Period finding
- Variability classification
- Transient detection

### Simulation and Modeling

**N-body Simulations**:
- Galaxy formation models
- Stellar dynamics
- Dark matter simulations

**Synthetic Observations**:
- Mock catalog generation
- Instrument simulation
- Survey planning


### Performance Optimization

!!! tip "Advanced: Resource Monitoring"
    - Use `canfar stats <session-id>` and `canfar info <session-id>` to monitor job resource usage.
    - For parallel workloads, see [Distributed Computing](../helpers/distributed.md).

#### Resource Allocation Strategy

**Right-sizing your jobs** is crucial for performance and queue times:

```bash
# Start small and scale up based on monitoring
# Test job with minimal resources first
canfar create \
  --name "test-small" \
  --cores 2 \
  --ram 4 \
  --image "images.canfar.net/skaha/astroml:latest" \
  --kind "headless" \
  --cmd "python /arc/projects/myproject/test_script.py"

# Monitor resource usage in the job logs
# Scale up for production runs if needed
```


**Memory Optimization:**
```python
# Memory-efficient data processing patterns
import numpy as np
from astropy.io import fits

def process_large_cube(filename):
    """Process large data cube efficiently"""
    
    # Memory-map large files instead of loading fully
    with fits.open(filename, memmap=True) as hdul:
        data = hdul[0].data
        
        # Process in chunks to control memory usage
        chunk_size = 100  # Adjust based on available RAM
        results = []
        
        for i in range(0, data.shape[0], chunk_size):
            chunk = data[i:i+chunk_size]
            # Process chunk and collect lightweight results
            result = np.mean(chunk, axis=(1,2))  # Example operation
            results.append(result)
            
            # Explicit cleanup for large chunks
            del chunk
            
        return np.concatenate(results)
```

**Storage Performance:**
```bash
# Use /scratch/ for I/O intensive operations
#!/bin/bash
set -e

# Copy data to fast scratch storage
echo "Copying data to scratch..."
rsync -av /arc/projects/myproject/large_dataset/ /scratch/working/

# Process on fast storage
cd /scratch/working
python intensive_processing.py

# Save results back to permanent storage
echo "Saving results..."
mkdir -p /arc/projects/myproject/results/$(date +%Y%m%d)
cp *.fits /arc/projects/myproject/results/$(date +%Y%m%d)/
cp *.log /arc/projects/myproject/logs/

echo "Processing complete"
```


#### Parallel Processing

!!! tip "Advanced: Distributed Workflows"
    - Use [Snakemake](https://snakemake.readthedocs.io/en/stable/) or [Prefect](https://www.prefect.io/) for complex workflow automation.
    - For team projects, see [Accounts & Permissions](accounts.md) for collaboration strategies.

**Multi-core CPU Usage:**
```python
from multiprocessing import Pool, cpu_count
import numpy as np
from functools import partial

def process_file(filename, parameters):
    """Process a single file"""
    # Your processing logic here
    return result

def parallel_processing():
    """Process multiple files in parallel"""
    
    # Get available CPU cores (leave 1 for system)
    n_cores = max(1, cpu_count() - 1)
    
    files = glob.glob('/scratch/input/*.fits')
    parameters = {'param1': value1, 'param2': value2}
    
    # Create partial function with fixed parameters
    process_func = partial(process_file, parameters=parameters)
    
    # Process files in parallel
    with Pool(n_cores) as pool:
        results = pool.map(process_func, files)
    
    return results
```

**GPU Acceleration (when available):**
```python
import numpy as np
try:
    import cupy as cp  # GPU arrays
    gpu_available = True
except ImportError:
    import numpy as cp  # Fallback to CPU
    gpu_available = False

def gpu_accelerated_processing(data):
    """Use GPU acceleration when available"""
    
    if gpu_available:
        print(f"Using GPU acceleration")
        # Convert to GPU array
        gpu_data = cp.asarray(data)
        
        # GPU-accelerated operations
        result = cp.fft.fft2(gpu_data)
        result = cp.abs(result)
        
        # Convert back to CPU for saving
        return cp.asnumpy(result)
    else:
        print("Using CPU fallback")
        # CPU-only operations
        return np.abs(np.fft.fft2(data))
```

#### Job Monitoring and Logging

**Comprehensive Logging:**
```python
import logging
import psutil
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/arc/projects/myproject/logs/processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_system_status():
    """Log current system resource usage"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/scratch')
    
    logger.info(f"CPU: {cpu_percent:.1f}%", 
                f"Memory: {memory.percent:.1f}% "
                f"({memory.used//1024**3:.1f}GB used), "
                f"Scratch: {disk.percent:.1f}% used")

def timed_processing(func, *args, **kwargs):
    """Wrapper to time and log function execution"""
    start_time = time.time()
    logger.info(f"Starting {func.__name__}")
    log_system_status()
    
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"Completed {func.__name__} in {elapsed:.2f} seconds")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed {func.__name__} after {elapsed:.2f} seconds: {e}")
        raise
```


---

!!! info "See Also"
    - [Container Development](containers.md)
    - [Storage Guide](guides/storage/index.md)
    - [CANFAR Python Client](../client/home.md)
    - [API Reference](https://ws-uv.canfar.net/skaha/v0/capabilities)
    - [Support](help.md)

### Job Sizing Guidelines

Choose appropriate resources based on your workload:

| Job Type | Cores | Memory | Storage | Duration |
|----------|-------|--------|---------|----------|
| Single image reduction | 1-2 | 4-8GB | 10GB | 5-30 min |
| Survey night processing | 4-8 | 16-32GB | 100GB | 1-4 hours |
| Catalog cross-matching | 2-4 | 8-16GB | 50GB | 30min-2hr |
| ML model training | 8-16 | 32-64GB | 200GB | 4-24 hours |
| Large simulations | 16-32 | 64-128GB | 1TB | Days-weeks |


!!! tip "Queue Optimization"
    - **Small jobs** (≤4 cores, ≤16GB) start faster
    - **Large jobs** (≥16 cores, ≥64GB) may queue longer  
    - **Off-peak hours** (evenings, weekends) often have shorter wait times
    - **Resource requests** should match actual usage to avoid waste
    - For advanced queue management, see [CANFAR Python Client](../client/home.md)

### Queue Management

Understand job priorities and scheduling:

- **Small jobs** (<4 cores, <16GB): Higher priority, faster start
- **Large jobs** (16+ cores, 64GB+): Lower priority, may queue longer
- **Off-peak hours**: Better resource availability (evenings, weekends)
- **Resource limits**: Per-user and per-group limits apply

## API Reference {#api-access}


!!! note "Legacy Client"
    The `skaha` Python client is deprecated and has been replaced by the `canfar` client. The following examples use the modern `canfar` client.
    For more examples, see [Client Examples](../client/examples.md).

### Method 1: `canfar` Command-Line Client

#### Submit Job

```bash
canfar create \
  --name "my-analysis-job" \
  --image "images.canfar.net/skaha/astroml:latest" \
  --cores 4 \
  --ram 16 \
  --cmd "python /arc/projects/myproject/analysis.py"
```

#### List Jobs

```bash
canfar ps
```

#### Get Job Status

```bash
canfar info <session-id>
```

#### Cancel Job

```bash
canfar delete <session-id>
```

#### Get Job Logs

```bash
canfar logs <session-id>
```

#### Get Resource Usage

```bash
canfar stats <session-id>
```

### Method 2: `canfar` Python Client

The `canfar` Python client provides a convenient interface for batch job management and automation.

#### Installation

```bash
pip install canfar
```

#### Basic Python Client Usage

```python
from canfar.sessions import Session

# Initialize session manager
session = Session()

# Simple job submission
job_ids = session.create(
    name="python-analysis",
    image="images.canfar.net/skaha/astroml:latest",
    kind="headless",
    cmd="python",
    args=["/arc/projects/myproject/analysis.py"]
)

print(f"Submitted job(s): {job_ids}")
```

#### Advanced Job Submission

```python
from canfar.sessions import Session

session = Session()

# Job with custom resources and environment
job_ids = session.create(
    name="heavy-computation",
    image="images.canfar.net/myproject/processor:latest", 
    kind="headless",
    cores=8,
    ram=32,
    cmd="/opt/scripts/heavy_process.sh",
    args=["/arc/projects/data/large_dataset.h5", "/arc/projects/results/"],
    env={
        "PROCESSING_THREADS": "8",
        "OUTPUT_FORMAT": "hdf5",
        "VERBOSE": "true"
    }
)
```

#### Private Image Authentication

To use private images, you first need to configure the client with your registry credentials. See the [authentication guide](accounts.md) for details.

#### Job Monitoring and Management

```python
import time
from canfar.sessions import Session

session = Session()

# List all your sessions
sessions = session.fetch()
print(f"Active sessions: {len(sessions)}")

# Create a job to monitor
job_ids = session.create(
    name="monitored-job",
    image="images.canfar.net/skaha/astroml:latest",
    kind="headless",
    cmd="sleep 60"
)
job_id = job_ids[0]

# Get session details
session_info = session.info(ids=job_id)
print(f"Status: {session_info[0]['status']}")
print(f"Start time: {session_info[0]['startTime']}")

# Wait for completion
while True:
    status = session.info(ids=job_id)[0]['status']
    if status in ['Succeeded', 'Failed', 'Terminated']:
        print(f"Job completed with status: {status}")
        break
    time.sleep(10)

# Get logs
logs = session.logs(ids=job_id)
print("Job output:")
print(logs[job_id])

# Clean up
session.destroy(ids=job_id)
```

#### Bulk Job Management

```python
from canfar.sessions import Session

session = Session()

# Submit multiple related jobs
job_ids = session.create(
    name="parameter-study",
    image="images.canfar.net/skaha/astroml:latest",
    kind="headless",
    cmd="python /arc/projects/study/analyze.py",
    replicas=10 # Creates 10 jobs named parameter-study-1, parameter-study-2, etc.
)
print(f"Submitted jobs: {job_ids}")

# Monitor all jobs
# ... (see single job monitoring example)
```



## Monitoring and Debugging

!!! tip "Advanced: Debugging Batch Jobs"
    - Use `canfar logs <session-id>` and `canfar stats <session-id>` for troubleshooting.
    - For persistent issues, see [FAQ](../faq.md) and [Support](help.md).

### Log Analysis

Monitor job progress through logs:

```bash
# Real-time log monitoring
canfar logs -f <session-id>

# Search for errors
canfar logs <session-id> | grep -i error
```

### Resource Monitoring

Track resource usage:

```bash
# Get session statistics
canfar stats <session-id>
```

### Common Issues

**Job fails to start**:
- Check resource availability
- Verify container image exists
- Check command syntax

**Job crashes**:
- Review logs for error messages
- Check memory usage patterns
- Verify input file accessibility

**Job hangs**:
- Monitor CPU usage
- Check for infinite loops
- Verify network connectivity


## Best Practices

!!! info "See Also"
    - [Container Development](containers.md)
    - [Storage Guide](guides/storage/index.md)
    - [CANFAR Python Client](../client/home.md)
    - [API Reference](https://ws-uv.canfar.net/skaha/v0/capabilities)
    - [Support](help.md)

### Script Design

- **Error handling**: Use try-catch blocks and meaningful error messages
- **Logging**: Include progress indicators and debugging information
- **Checkpointing**: Save intermediate results for long-running jobs
- **Resource monitoring**: Track memory and CPU usage

### Data Management

- **Input validation**: Check file existence and format before processing
- **Output organization**: Use consistent naming and directory structures
- **Cleanup**: Remove temporary files to save storage
- **Metadata**: Include processing parameters in output headers


!!! warning "Persistence Reminder"
    Headless containers do not persist changes to the container filesystem. Always write outputs to `/arc/projects/` or `/arc/home/`.
    For data management strategies, see [Storage Guide](guides/storage/index.md).

### Security and Efficiency

- **Token management**: Use secure token storage and rotation
- **Resource limits**: Don't request more resources than needed
- **Parallel processing**: Use appropriate parallelization strategies
- **Cost optimization**: Run large jobs during off-peak hours


## Getting Help

!!! info "Quick Links"
    - [Support](help.md)
    - [FAQ](../faq.md)
    - [Client Examples](../client/examples.md)
    - [Discord Community](https://discord.gg/vcCQ8QBvBa)

- **API Documentation**: [CANFAR API Reference](https://ws-uv.canfar.net/skaha/v0/capabilities)
- **Support**: Email [support@canfar.net](mailto:support@canfar.net)
- **Community**: Join our Discord for batch processing discussions
- **Examples**: Check the [CANFAR GitHub](https://github.com/opencadc) for more examples

## Next Steps

- **[Container Development](containers.md)**: Build custom containers for your workflows
- **[Storage Optimization](guides/storage/index.md)**: Efficient data management strategies
- **[Interactive Sessions](guides/interactive-sessions/index.md)**: Develop and test scripts interactively
- **[Radio Astronomy Workflows](guides/radio-astronomy/index.md)**: Specialized batch processing for radio data
