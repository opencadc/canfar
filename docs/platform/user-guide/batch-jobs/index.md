# Batch Jobs and Headless Processing

Batch jobs enable automated, non-interactive processing of astronomical data at scale. This section covers headless execution, API access, job scheduling, and workflow automation on the CANFAR Science Platform.

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

## Batch Processing Methods

### 1. API-Based Execution

Execute containers programmatically using the CANFAR API:

```bash
# Submit a job via API
curl -X POST "https://ws-uv.canfar.net/skaha/v0/session" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=data-reduction-job" \
  -d "image=images.canfar.net/skaha/astroml:latest" \
  -d "cores=4" \
  -d "ram=16" \
  -d "kind=headless" \
  -d "cmd=python /arc/projects/myproject/scripts/reduce_data.py"
```

### 2. Job Submission Scripts

Create shell scripts for common workflows using the API or Python client:

```bash
#!/bin/bash
# submit_reduction.sh - API-based job submission

# Set job parameters
JOB_NAME="nightly-reduction-$(date +%Y%m%d)"
IMAGE="images.canfar.net/skaha/casa:6.5"
CMD="python /arc/projects/survey/pipelines/reduce_night.py /arc/projects/survey/data/$(date +%Y%m%d)"

# Submit job via API
curl -X POST "https://ws-uv.canfar.net/skaha/v0/session" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=$JOB_NAME" \
  -d "image=$IMAGE" \
  -d "cores=8" \
  -d "ram=32" \
  -d "kind=headless" \
  -d "cmd=$CMD"
```

Or using the Python skaha client:

```python
#!/usr/bin/env python3
# submit_reduction.py - Python client-based submission

from skaha.session import Session
from datetime import datetime

# Initialize session manager
session = Session()

# Set job parameters
job_name = f"nightly-reduction-{datetime.now().strftime('%Y%m%d')}"
image = "images.canfar.net/skaha/casa:6.5"
data_path = f"/arc/projects/survey/data/{datetime.now().strftime('%Y%m%d')}"

# Submit job
job_id = session.create(
    name=job_name,
    image=image,
    kind="headless",
    cores=8,
    ram=32,
    cmd="python",
    args=["/arc/projects/survey/pipelines/reduce_night.py", data_path]
)

print(f"Submitted job: {job_id}")
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

## Resource Planning

### Job Sizing

Choose appropriate resources based on your workload:

| Job Type | Cores | Memory | Storage | Duration |
|----------|-------|--------|---------|----------|
| Single image reduction | 1-2 | 4-8GB | 10GB | 5-30 min |
| Survey night processing | 4-8 | 16-32GB | 100GB | 1-4 hours |
| Catalog cross-matching | 2-4 | 8-16GB | 50GB | 30min-2hr |
| ML model training | 8-16 | 32-64GB | 200GB | 4-24 hours |
| Large simulations | 16-32 | 64-128GB | 1TB | Days-weeks |

### Queue Management

Understand job priorities and scheduling:

- **Small jobs** (<4 cores, <16GB): Higher priority, faster start
- **Large jobs** (16+ cores, 64GB+): Lower priority, may queue longer
- **Off-peak hours**: Better resource availability (evenings, weekends)
- **Resource limits**: Per-user and per-group limits apply

## API Reference {#api-access}

### Method 1: Direct curl Commands

#### Submit Job

```bash
curl -X POST "https://ws-uv.canfar.net/skaha/v0/session" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=my-analysis-job" \
  -d "image=images.canfar.net/skaha/astroml:latest" \
  -d "cores=4" \
  -d "ram=16" \
  -d "kind=headless" \
  -d "cmd=python /arc/projects/myproject/analysis.py"
```

#### List Jobs

```bash
curl -X GET "https://ws-uv.canfar.net/skaha/v0/session" \
  -H "Authorization: Bearer $TOKEN"
```

#### Get Job Status

```bash
curl -X GET "https://ws-uv.canfar.net/skaha/v0/session/{session-id}" \
  -H "Authorization: Bearer $TOKEN"
```

#### Cancel Job

```bash
curl -X DELETE "https://ws-uv.canfar.net/skaha/v0/session/{session-id}" \
  -H "Authorization: Bearer $TOKEN"
```

#### Get Job Logs

```bash
curl -X GET "https://ws-uv.canfar.net/skaha/v0/session/{session-id}/logs" \
  -H "Authorization: Bearer $TOKEN"
```

#### Get Resource Usage

```bash
curl -X GET "https://ws-uv.canfar.net/skaha/v0/session/{session-id}/stats" \
  -H "Authorization: Bearer $TOKEN"
```

### Method 2: Python skaha Client

The [skaha](https://shinybrar.github.io/skaha/latest/) Python client provides a more convenient interface for batch job management and automation.

#### Installation

```bash
mamba activate base
pip install skaha
```

#### Basic Python Client Usage

```python
from skaha.session import Session
from skaha.image import Image
import time

# Initialize session manager
session = Session()

# Simple job submission
job_id = session.create(
    name="python-analysis",
    image="images.canfar.net/skaha/astroml:latest",
    kind="headless",
    cmd="python",
    args=["/arc/projects/myproject/analysis.py"]
)

print(f"Submitted job: {job_id}")
```

#### Advanced Job Submission

```python
# Job with custom resources and environment
job_id = session.create(
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

```python
# For private images, set registry authentication
import base64

username = "your_username"
cli_secret = "your_cli_secret"
auth_string = base64.b64encode(f"{username}:{cli_secret}".encode()).decode()

job_id = session.create(
    name="private-image-job",
    image="images.canfar.net/myproject/private:latest",
    kind="headless",
    cmd="python /opt/analysis.py",
    registry_auth=auth_string
)
```

#### Job Monitoring and Management

```python
# List all your sessions
sessions = session.fetch()
print(f"Active sessions: {len(sessions)}")

# Get session details
session_info = session.fetch(job_id)
print(f"Status: {session_info['status']}")
print(f"Start time: {session_info['startTime']}")

# Wait for completion
while True:
    status = session.fetch(job_id)['status']
    if status in ['Succeeded', 'Failed', 'Terminated']:
        print(f"Job completed with status: {status}")
        break
    time.sleep(30)

# Get logs
logs = session.logs(job_id)
print("Job output:")
print(logs)

# Clean up
session.delete(job_id)
```

#### Bulk Job Management

```python
# Submit multiple related jobs
job_ids = []
for i in range(10):
    job_id = session.create(
        name=f"parameter-study-{i}",
        image="images.canfar.net/skaha/astroml:latest",
        kind="headless",
        cmd="python",
        args=["/arc/projects/study/analyze.py", f"--param={i}"]
    )
    job_ids.append(job_id)
    print(f"Submitted job {i}: {job_id}")

# Monitor all jobs
completed = 0
while completed < len(job_ids):
    completed = 0
    for job_id in job_ids:
        status = session.fetch(job_id)['status']
        if status in ['Succeeded', 'Failed', 'Terminated']:
            completed += 1
    
    print(f"Completed: {completed}/{len(job_ids)}")
    if completed < len(job_ids):
        time.sleep(60)

print("All jobs completed!")
```

### Method 3: Higher-Level Python API

```python
# Example: Higher-level API for common tasks
from skaha import Session

# Create a session object
session = Session()

# Submit a data reduction job
job_id = session.submit(
    name="data-reduction",
    image="images.canfar.net/skaha/astroml:latest",
    cmd="python /arc/projects/myproject/scripts/reduce_data.py",
    cores=4,
    ram=16
)

# Monitor the job
session.monitor(job_id)

# Fetch and print logs
logs = session.logs(job_id)
print(logs)

# Delete the job after completion
session.delete(job_id)
```

## Workflow Examples

### Example 1: Automated Data Reduction

```python
#!/usr/bin/env python3
"""
Automated optical imaging reduction pipeline
Usage: python reduce_images.py --night 20240115
"""

import argparse
import os
import sys
from pathlib import Path
from astropy.io import fits
from photutils import detect_sources, source_properties

def main():
    parser = argparse.ArgumentParser(description='Reduce nightly observations')
    parser.add_argument('--night', required=True, help='Night to process (YYYYMMDD)')
    parser.add_argument('--filter', default='all', help='Filter to process')
    args = parser.parse_args()
    
    # Set up paths
    data_dir = Path(f"/arc/projects/survey/data/{args.night}")
    output_dir = Path(f"/arc/projects/survey/reduced/{args.night}")
    output_dir.mkdir(exist_ok=True)
    
    # Find raw images
    if args.filter == 'all':
        images = list(data_dir.glob("*.fits"))
    else:
        images = list(data_dir.glob(f"*{args.filter}*.fits"))
    
    print(f"Processing {len(images)} images for {args.night}")
    
    for image_path in images:
        try:
            # Load and process image
            with fits.open(image_path) as hdul:
                data = hdul[0].data
                header = hdul[0].header
            
            # Perform calibration (simplified)
            calibrated = calibrate_image(data, header)
            
            # Extract sources
            sources = extract_sources(calibrated)
            
            # Save results
            output_path = output_dir / f"reduced_{image_path.name}"
            save_reduced_image(calibrated, header, output_path)
            
            # Save catalog
            catalog_path = output_dir / f"catalog_{image_path.stem}.fits"
            save_catalog(sources, catalog_path)
            
            print(f"Processed {image_path.name}: {len(sources)} sources")
            
        except Exception as e:
            print(f"Error processing {image_path.name}: {e}")
            continue
    
    print(f"Reduction complete. Results in {output_dir}")

def calibrate_image(data, header):
    """Apply bias, dark, and flat field corrections"""
    # Implementation would go here
    return data

def extract_sources(data):
    """Extract and measure sources"""
    # Implementation would go here
    return []

def save_reduced_image(data, header, output_path):
    """Save calibrated image"""
    fits.writeto(output_path, data, header, overwrite=True)

def save_catalog(sources, output_path):
    """Save source catalog"""
    # Implementation would go here
    pass

if __name__ == "__main__":
    main()
```

### Example 2: Parameter Study

```python
#!/usr/bin/env python3
"""
Run parameter study for photometric analysis
"""

import json
import requests
import time
from itertools import product

# Parameter grid
aperture_sizes = [3, 5, 7, 10]  # pixels
sky_annuli = [(10, 15), (15, 20), (20, 25)]
detection_thresholds = [3.0, 5.0, 7.0]

# API configuration
API_BASE = "https://ws-uv.canfar.net/skaha/v0"
TOKEN = "your-token-here"

def submit_job(params):
    """Submit a single parameter combination job"""
    
    cmd = (f"python /arc/projects/survey/scripts/photometry.py "
           f"--aperture {params['aperture']} "
           f"--sky-inner {params['sky_inner']} "
           f"--sky-outer {params['sky_outer']} "
           f"--threshold {params['threshold']} "
           f"--output /arc/projects/survey/results/param_study_{params['job_id']}.fits")
    
    payload = {
        'name': f"photometry-study-{params['job_id']}",
        'image': 'images.canfar.net/skaha/astroml:latest',
        'cores': 2,
        'ram': 8,
        'kind': 'headless',
        'cmd': cmd
    }
    
    response = requests.post(
        f"{API_BASE}/session",
        headers={"Authorization": f"Bearer {TOKEN}"},
        data=payload
    )
    
    if response.status_code == 200:
        return response.json()['sessionId']
    else:
        print(f"Failed to submit job {params['job_id']}: {response.text}")
        return None

def main():
    """Submit all parameter combinations"""
    
    job_ids = []
    job_id = 0
    
    # Generate all parameter combinations
    for aperture, (sky_inner, sky_outer), threshold in product(
        aperture_sizes, sky_annuli, detection_thresholds
    ):
        params = {
            'job_id': job_id,
            'aperture': aperture,
            'sky_inner': sky_inner,
            'sky_outer': sky_outer,
            'threshold': threshold
        }
        
        session_id = submit_job(params)
        if session_id:
            job_ids.append((job_id, session_id))
            print(f"Submitted job {job_id}: {params}")
        
        job_id += 1
        time.sleep(1)  # Rate limiting
    
    print(f"Submitted {len(job_ids)} jobs")
    
    # Save job tracking info
    with open('/arc/projects/survey/param_study_jobs.json', 'w') as f:
        json.dump(job_ids, f)

if __name__ == "__main__":
    main()
```

## Monitoring and Debugging

### Log Analysis

Monitor job progress through logs:

```bash
# Real-time log monitoring
curl -s "https://ws-uv.canfar.net/skaha/v0/session/$SESSION_ID/logs" \
  -H "Authorization: Bearer $TOKEN" | tail -f

# Search for errors
curl -s "https://ws-uv.canfar.net/skaha/v0/session/$SESSION_ID/logs" \
  -H "Authorization: Bearer $TOKEN" | grep -i error
```

### Resource Monitoring

Track resource usage:

```bash
# Get session statistics
curl -s "https://ws-uv.canfar.net/skaha/v0/session/$SESSION_ID/stats" \
  -H "Authorization: Bearer $TOKEN" | jq .
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

### Security and Efficiency

- **Token management**: Use secure token storage and rotation
- **Resource limits**: Don't request more resources than needed
- **Parallel processing**: Use appropriate parallelization strategies
- **Cost optimization**: Run large jobs during off-peak hours

## Getting Help

- **API Documentation**: [CANFAR API Reference](https://ws-uv.canfar.net/skaha/v0/capabilities)
- **Support**: Email [support@canfar.net](mailto:support@canfar.net)
- **Community**: Join our Discord for batch processing discussions
- **Examples**: Check the [CANFAR GitHub](https://github.com/opencadc) for more examples

## Next Steps

- **[Container Development](../containers/index.md)**: Build custom containers for your workflows
- **[Storage Optimization](../storage/index.md)**: Efficient data management strategies
- **[Interactive Sessions](../interactive-sessions/index.md)**: Develop and test scripts interactively
- **[Radio Astronomy Workflows](../radio-astronomy/index.md)**: Specialized batch processing for radio data