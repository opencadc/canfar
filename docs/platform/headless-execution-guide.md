# Headless Container Execution Guide

> **📚 Related Guides:**
>
> - [Container Building Guide →](container-building-guide.md) - Create custom headless containers
> - [Storage Systems Guide →](storage-systems-guide.md) - Understand data storage for batch jobs
> - [Data Transfer Guide →](data-transfer-guide.md) - Move large datasets for processing
> - [skaha API Documentation →](https://shinybrar.github.io/skaha/latest/) - Complete API reference

This guide covers how to run headless containers on the CANFAR Science Platform using both curl commands and the skaha Python client for batch processing and automation.

!!! info "skaha Documentation"
    For complete API reference and advanced usage, see the [official skaha documentation](https://shinybrar.github.io/skaha/latest/).

## Overview

Headless containers are designed for:

- **Batch Processing**: Large-scale data analysis without user interaction
- **Automation**: Scheduled or triggered processing workflows  
- **Command-Line Tools**: Running CLI applications remotely
- **API Integration**: Programmatic job submission and monitoring

**Use Cases:**

- Processing ALMA datacubes in batch
- Running parameter sweeps for simulations  
- Automated data pipeline execution
- Large-scale survey data reduction

> **💡 Storage Tip:** For batch processing workflows, use `/scratch/` for temporary files and `/arc/projects/` for results. See the [Storage Systems Guide](storage-systems-guide.md) for optimal data placement strategies.

## Prerequisites

### Authentication Setup

All headless execution requires CADC authentication:

1. **CADC Proxy Certificate** (for curl):

   ```bash
   # Get your proxy certificate
   cadc-get-cert -u your_username
   # Certificate saved to ~/.ssl/cadcproxy.pem
   ```

2. **Harbor Registry Access** (for private images):

   - Login to <https://images.canfar.net>
   - Go to User Profile → CLI Secret
   - Copy your CLI secret for authentication

### Environment Setup

Before using headless containers, activate your environment:

```bash
mamba activate base
```

## Method 1: Using curl Commands

### Basic Headless Job Submission

#### Public Images

```bash
# Simple command execution
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session \
  -d "name=my-analysis" \
  -d "image=images.canfar.net/skaha/astroconda:latest" \
  -d "kind=headless" \
  --data-urlencode "cmd=python" \
  --data-urlencode "args=-c 'print(\"Hello from headless container\")'"
```

#### Private Images

```bash
# Create authentication header
ENCODED_HEADER=$(echo -n "your_username:your_cli_secret" | base64 -i -)

# Submit job with authentication
curl --header "x-skaha-registry-auth: ${ENCODED_HEADER}" \
  -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session \
  -d "name=private-analysis" \
  -d "image=images.canfar.net/myproject/analyzer:latest" \
  -d "kind=headless" \
  --data-urlencode "cmd=/opt/scripts/process.sh" \
  --data-urlencode "args=/arc/projects/myproject/data/input.fits"
```

### Advanced Job Configuration

#### Resource Specification

```bash
# Request specific CPU and memory
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session \
  -d "name=big-analysis" \
  -d "image=images.canfar.net/skaha/scipy:latest" \
  -d "kind=headless" \
  -d "cores=4" \
  -d "ram=16" \
  --data-urlencode "cmd=python" \
  --data-urlencode "args=/arc/projects/survey/process_large_dataset.py"
```

#### Environment Variables

```bash
# Pass environment variables to container
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session \
  -d "name=parameterized-job" \
  -d "image=images.canfar.net/astro/pipeline:latest" \
  -d "kind=headless" \
  -d "env=PROCESSING_MODE=batch" \
  -d "env=OUTPUT_FORMAT=fits" \
  -d "env=VERBOSE=true" \
  --data-urlencode "cmd=/opt/pipeline/run.sh"
```

#### Multiple Arguments

```bash
# Complex command with multiple arguments
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session \
  -d "name=multi-arg-job" \
  -d "image=images.canfar.net/tools/processor:latest" \
  -d "kind=headless" \
  --data-urlencode "cmd=python" \
  --data-urlencode "args=/opt/scripts/analyze.py --input /arc/projects/data/raw.fits --output /arc/projects/results/ --format json --verbose --threads 4"
```

### Job Monitoring with curl

#### List All Sessions

```bash
# View all your sessions and jobs
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session
```

#### Check Specific Job Status

```bash
# View single session details
SESSION_ID="your-session-id"
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session/${SESSION_ID}
```

#### View Job Logs

```bash
# Get complete output (stdout and stderr)
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session/${SESSION_ID}?view=logs
```

#### Check Scheduling Events

```bash
# View scheduling issues (if any)
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session/${SESSION_ID}?view=events
```

#### Delete/Cancel Job

```bash
# Terminate running job
curl -E ~/.ssl/cadcproxy.pem \
  -X DELETE \
  https://ws-uv.canfar.net/skaha/v0/session/${SESSION_ID}
```

## Method 2: Using skaha Python Client

### Installation

```bash
mamba activate base
pip install skaha-client
```

### Basic Python Client Usage

#### Import and Setup

```python
from skaha.session import Session
from skaha.image import Image
import time

# Initialize session manager
session = Session()
```

#### Submit Headless Jobs

```python
# Simple job submission
job_id = session.create(
    name="python-analysis",
    image="images.canfar.net/skaha/astroconda:latest",
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
    name="private-job",
    image="images.canfar.net/private/analyzer:latest",
    kind="headless", 
    cmd="/opt/private/analyze",
    registry_auth=auth_string
)
```

### Job Monitoring with Python

#### Check Job Status

```python
# Get job details
job_info = session.get(job_id)
print(f"Status: {job_info['phase']}")
print(f"Start time: {job_info.get('startTime', 'Not started')}")
```

#### Wait for Completion

```python
# Poll until job completes
def wait_for_completion(session, job_id, polling_interval=30):
    """Wait for job to complete, polling every interval seconds"""
    while True:
        job_info = session.get(job_id)
        phase = job_info['phase']
        
        print(f"Job {job_id} status: {phase}")
        
        if phase in ['Succeeded', 'Failed', 'Unknown']:
            return phase
            
        time.sleep(polling_interval)

# Use the function
final_status = wait_for_completion(session, job_id)
print(f"Job completed with status: {final_status}")
```

#### Get Job Logs

```python
# Retrieve job output
try:
    logs = session.get_logs(job_id)
    print("Job Output:")
    print(logs)
except Exception as e:
    print(f"Error getting logs: {e}")
```

#### List All Jobs

```python
# Get all your sessions
all_sessions = session.list()

# Filter headless jobs
headless_jobs = [s for s in all_sessions if s.get('kind') == 'headless']

for job in headless_jobs:
    print(f"Job: {job['name']} - Status: {job['phase']}")
```

## Practical Examples

### Example 1: Astronomy Data Processing

```python
# Process a list of FITS files
from skaha.session import Session

session = Session()
input_files = [
    "/arc/projects/survey/raw/field001.fits",
    "/arc/projects/survey/raw/field002.fits", 
    "/arc/projects/survey/raw/field003.fits"
]

job_ids = []
for i, input_file in enumerate(input_files):
    job_id = session.create(
        name=f"process-field-{i+1:03d}",
        image="images.canfar.net/astro/photometry:latest",
        kind="headless",
        cores=2,
        ram=8,
        cmd="python",
        args=[
            "/opt/photometry/process.py",
            "--input", input_file,
            "--output", f"/arc/projects/survey/processed/field{i+1:03d}_processed.fits",
            "--catalog", "/arc/projects/survey/catalogs/reference.cat"
        ],
        env={"PROCESSING_MODE": "batch", "VERBOSE": "true"}
    )
    job_ids.append(job_id)
    print(f"Submitted processing job for {input_file}: {job_id}")

# Monitor all jobs
print("Monitoring jobs...")
completed_jobs = []
while len(completed_jobs) < len(job_ids):
    for job_id in job_ids:
        if job_id not in completed_jobs:
            status = session.get(job_id)['phase']
            if status in ['Succeeded', 'Failed']:
                completed_jobs.append(job_id)
                print(f"Job {job_id} completed with status: {status}")
    time.sleep(60)  # Check every minute

print("All jobs completed!")
```

### Example 2: Batch curl Script

```bash
#!/bin/bash
# batch_process.sh - Submit multiple headless jobs

set -e

# Configuration
IMAGE="images.canfar.net/astro/casa:latest"
INPUT_DIR="/arc/projects/radio/raw"
OUTPUT_DIR="/arc/projects/radio/processed"

# Get list of input files
FILES=$(find ${INPUT_DIR} -name "*.ms" -type d)

echo "Submitting batch jobs for CASA processing..."

JOB_IDS=()
for msfile in $FILES; do
    basename=$(basename "$msfile" .ms)
    
    echo "Submitting job for: $basename"
    
    # Submit job and capture session ID
    SESSION_ID=$(curl -s -E ~/.ssl/cadcproxy.pem \
        https://ws-uv.canfar.net/skaha/v0/session \
        -d "name=casa-${basename}" \
        -d "image=${IMAGE}" \
        -d "kind=headless" \
        -d "cores=4" \
        -d "ram=16" \
        --data-urlencode "cmd=casa" \
        --data-urlencode "args=--nogui --nologger -c /opt/scripts/process_ms.py ${msfile} ${OUTPUT_DIR}/${basename}" \
        | python -c "import sys, json; print(json.load(sys.stdin)['sessionId'])")
    
    JOB_IDS+=("$SESSION_ID")
    echo "  Submitted: $SESSION_ID"
done

echo "Submitted ${#JOB_IDS[@]} jobs"
echo "Job IDs: ${JOB_IDS[*]}"

# Monitor jobs
echo "Monitoring job completion..."
while true; do
    completed=0
    for job_id in "${JOB_IDS[@]}"; do
        status=$(curl -s -E ~/.ssl/cadcproxy.pem \
            https://ws-uv.canfar.net/skaha/v0/session/${job_id} \
            | python -c "import sys, json; print(json.load(sys.stdin)['phase'])")
        
        if [[ "$status" == "Succeeded" || "$status" == "Failed" ]]; then
            ((completed++))
        fi
    done
    
    echo "Progress: $completed/${#JOB_IDS[@]} jobs completed"
    
    if [ $completed -eq ${#JOB_IDS[@]} ]; then
        echo "All jobs completed!"
        break
    fi
    
    sleep 300  # Check every 5 minutes
done
```

## Job States and Lifecycle

### Job Phases

- **Pending**: Job submitted, waiting for resources
- **Running**: Job is executing
- **Succeeded**: Job completed successfully (exit code 0)
- **Failed**: Job failed (non-zero exit code)
- **Terminating**: Job is being stopped
- **Unknown**: Job state cannot be determined

### Job Lifecycle

1. **Submission**: Job sent to scheduler
2. **Queuing**: Waiting for available resources
3. **Scheduling**: Resources allocated, container starting
4. **Execution**: Container running your command
5. **Completion**: Container exits, logs available
6. **Cleanup**: Job removed after 1 hour

## Practical Examples with curl

### Example 1: Astronomy Data Processing with curl

Process ALMA data cubes using CASA:

```bash
# Submit CASA processing job
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session \
  -d "name=alma-imaging" \
  -d "image=images.canfar.net/skaha/casa:latest" \
  -d "kind=headless" \
  -d "cores=8" \
  -d "ram=32" \
  --data-urlencode "cmd=casa" \
  --data-urlencode "args=--nologger --log2term --nogui -c /arc/projects/alma/scripts/imaging_pipeline.py"
```

Response:
```json
{
  "id": "abc123-imaging-session",
  "userid": "username",
  "name": "alma-imaging",
  "phase": "Pending"
}
```

Monitor progress:
```bash
# Check job status
SESSION_ID="abc123-imaging-session"
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session/${SESSION_ID}

# View processing logs
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session/${SESSION_ID}?view=logs
```

### Example 2: Python Analysis with skaha Client

Complete workflow using the Python client:

```python
from skaha.session import Session
import time
import os

# Initialize client
session = Session()

# Submit data analysis job
job_id = session.create(
    name="stellar-analysis",
    image="images.canfar.net/skaha/scipy:latest",
    kind="headless",
    cores=4,
    ram=16,
    cmd="python",
    args=["/arc/projects/survey/scripts/stellar_photometry.py", 
          "--input", "/arc/projects/survey/data/field001.fits",
          "--output", "/arc/projects/survey/results/",
          "--catalog", "/arc/projects/survey/catalogs/stars.csv",
          "--threads", "4"],
    env={
        "PYTHONPATH": "/arc/projects/survey/lib",
        "OMP_NUM_THREADS": "4"
    }
)

print(f"Submitted job: {job_id}")

# Monitor until completion
while True:
    status = session.get(job_id)
    phase = status['phase']
    print(f"Status: {phase}")
    
    if phase == 'Succeeded':
        print("✅ Analysis completed successfully!")
        logs = session.get_logs(job_id)
        print("Final output:")
        print(logs[-500:])  # Last 500 characters
        break
    elif phase == 'Failed':
        print("❌ Job failed!")
        logs = session.get_logs(job_id)
        print("Error logs:")
        print(logs)
        break
    elif phase in ['Running', 'Pending']:
        time.sleep(60)  # Check every minute
    else:
        print(f"Unknown phase: {phase}")
        break
```

### Example 3: Batch Processing Multiple Files

Process a series of FITS files using curl:

```bash
#!/bin/bash
# batch_process.sh - Process multiple files

# Array of input files
files=(
    "observation_001.fits"
    "observation_002.fits" 
    "observation_003.fits"
)

# Submit jobs for each file
for file in "${files[@]}"; do
    echo "Processing $file..."
    
    job_response=$(curl -s -E ~/.ssl/cadcproxy.pem \
        https://ws-uv.canfar.net/skaha/v0/session \
        -d "name=process-${file%.fits}" \
        -d "image=images.canfar.net/astro/processor:latest" \
        -d "kind=headless" \
        -d "cores=2" \
        -d "ram=8" \
        --data-urlencode "cmd=/opt/scripts/fits_processor.py" \
        --data-urlencode "args=--input /arc/projects/data/$file --output /arc/projects/results/processed_$file")
    
    job_id=$(echo $job_response | jq -r '.id')
    echo "Submitted job: $job_id"
    
    # Small delay between submissions
    sleep 2
done

echo "All jobs submitted!"
```

### Example 4: Parameter Sweep with Python

Run parameter sweep for simulation:

```python
from skaha.session import Session
import itertools
import time

session = Session()
job_ids = []

# Parameter ranges
temperatures = [100, 200, 300, 400, 500]
pressures = [1.0, 2.0, 3.0, 4.0, 5.0]

# Submit job for each parameter combination
for temp, press in itertools.product(temperatures, pressures):
    job_id = session.create(
        name=f"sim-T{temp}-P{press}",
        image="images.canfar.net/physics/simulator:latest",
        kind="headless",
        cores=2,
        ram=4,
        cmd="/opt/simulation/run_sim",
        args=[
            "--temperature", str(temp),
            "--pressure", str(press),
            "--output", f"/arc/projects/sims/results/T{temp}_P{press}.h5",
            "--steps", "10000"
        ],
        env={
            "CUDA_VISIBLE_DEVICES": "",  # CPU only
            "OMP_NUM_THREADS": "2"
        }
    )
    
    job_ids.append((job_id, temp, press))
    print(f"Submitted T={temp}K, P={press}atm: {job_id}")
    
    # Throttle submissions
    time.sleep(1)

print(f"Submitted {len(job_ids)} jobs total")

# Monitor completion
completed = 0
while completed < len(job_ids):
    for job_id, temp, press in job_ids:
        status = session.get(job_id)
        if status['phase'] == 'Succeeded':
            print(f"✅ Completed: T={temp}K, P={press}atm")
            completed += 1
        elif status['phase'] == 'Failed':
            print(f"❌ Failed: T={temp}K, P={press}atm")
            completed += 1
    
    time.sleep(30)  # Check every 30 seconds

print("Parameter sweep complete!")
```

### Example 5: Using Private Container Registry

Submit job with private image authentication:

```bash
# Create authentication header
USERNAME="your_username"
CLI_SECRET="your_cli_secret"
ENCODED_HEADER=$(echo -n "${USERNAME}:${CLI_SECRET}" | base64)

# Submit job using private container
curl --header "x-skaha-registry-auth: ${ENCODED_HEADER}" \
  -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session \
  -d "name=private-analysis" \
  -d "image=images.canfar.net/myproject/proprietary-tool:v2.1" \
  -d "kind=headless" \
  -d "cores=4" \
  -d "ram=16" \
  --data-urlencode "cmd=/opt/proprietary/analyze" \
  --data-urlencode "args=--config /arc/projects/myproject/config.yaml --data /arc/projects/myproject/datasets/large_survey.h5"
```

Python equivalent:
```python
import base64
from skaha.session import Session

# Setup authentication
username = "your_username"
cli_secret = "your_cli_secret" 
auth_string = base64.b64encode(f"{username}:{cli_secret}".encode()).decode()

session = Session()
job_id = session.create(
    name="private-analysis",
    image="images.canfar.net/myproject/proprietary-tool:v2.1",
    kind="headless",
    cores=4,
    ram=16,
    cmd="/opt/proprietary/analyze",
    args=["--config", "/arc/projects/myproject/config.yaml", 
          "--data", "/arc/projects/myproject/datasets/large_survey.h5"],
    registry_auth=auth_string
)
```

## Best Practices

### Job Design

- **Stateless**: Design jobs to be independent and repeatable
- **Idempotent**: Jobs should produce same results if re-run
- **Error Handling**: Include proper error checking and logging
- **Resource Estimates**: Request appropriate CPU/memory resources

### Data Management

- **Input Validation**: Check input files exist before processing
- **Output Organization**: Use consistent naming and directory structure  
- **Intermediate Files**: Clean up temporary files to save space (use `/scratch/` for temp files)
- **Logging**: Write detailed logs for debugging

> **📂 Storage Strategy:** Store raw data in `/arc/projects/`, process in `/scratch/` for speed, and save results back to `/arc/projects/`. See [Storage Systems Guide](storage-systems-guide.md) for details.

### Performance

- **Resource Monitoring**: Use `htop` and `df` to monitor usage
- **Parallel Processing**: Utilize multiple cores when possible
- **Memory Management**: Stream large datasets rather than loading entirely
- **Storage Optimization**: Use `/scratch/` for temporary high-speed processing

> **⚡ Performance Tip:** Download large datasets to `/scratch/` in your headless container for fastest I/O, then copy results to `/arc/projects/`. See [Storage Performance](storage-systems-guide.md#performance-tips) for details.

### Error Recovery

- **Exit Codes**: Always return proper exit codes (0=success, 1-255=error)
- **Retry Logic**: Design for automatic retry capabilities
- **Partial Results**: Save intermediate outputs for long-running jobs
- **Logging Strategy**: Include timestamps and error context

## Troubleshooting

### Common Issues

#### Job Stuck in Pending

1. **Check CLI Secret**: Reset in Harbor registry profile
2. **Verify permissions**: Ensure access to container image
3. **Resource availability**: Platform may be waiting for resources
4. **Image problems**: Verify image exists and is correctly tagged

#### Job Fails Immediately

```bash
# Check job events for scheduling issues
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session/${SESSION_ID}?view=events

# Review complete logs
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session/${SESSION_ID}?view=logs
```

#### Authentication Problems

- **Proxy Certificate**: Ensure `cadc-get-cert` is current and valid
- **Harbor Access**: Check CLI secret is correctly configured
- **Network Issues**: Verify VPN or network connectivity

#### Resource Issues

- **Out of Memory**: Request more RAM or optimize algorithm
- **CPU Limits**: Verify core count matches processing needs
- **Storage Full**: Check `/arc` and `/scratch` disk usage

### Getting Help

For headless job issues:

- **Quick help**: [CANFAR Slack channel](https://cadc.slack.com/archives/C01K60U5Q87)
- **Technical issues**: Email [support@canfar.net](mailto:support@canfar.net)
- **API documentation**: [skaha documentation](https://shinybrar.github.io/skaha/latest/)
- **Bug reports**: [GitHub issues](https://github.com/opencadc/skaha/issues)

## Migration from Legacy Batch Systems

### From SLURM/PBS Scripts

Transform traditional HPC job scripts to CANFAR headless:

**Traditional SLURM**:

```bash
#!/bin/bash
#SBATCH --job-name=analysis
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

module load python/3.9
python analysis.py input.dat output.txt
```

**CANFAR Equivalent**:

```bash
# Submit as headless job
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session \
  -d "name=analysis" \
  -d "image=images.canfar.net/skaha/astroconda:latest" \
  -d "kind=headless" \
  -d "cores=4" \
  -d "ram=8" \
  --data-urlencode "cmd=python" \
  --data-urlencode "args=/arc/projects/myproject/analysis.py /arc/projects/myproject/input.dat /arc/projects/myproject/output.txt"
```

### From Docker Scripts

Convert existing containerized workflows:

**Local Docker**:

```bash
docker run -v /local/data:/data myimage:latest \
  python process.py /data/input /data/output
```

**CANFAR Headless**:

```python
from skaha.session import Session

session = Session()
job_id = session.create(
    name="containerized-processing",
    image="images.canfar.net/myproject/myimage:latest",
    kind="headless",
    cmd="python",
    args=["process.py", "/arc/projects/myproject/input", "/arc/projects/myproject/output"]
)
```

---

**Related Documentation:**

- [Container Building Guide](container-building-guide.md) - Create custom processing containers
- [Storage Systems Guide](storage-systems-guide.md) - Understand data storage options
- [skaha Python Client Documentation](https://shinybrar.github.io/skaha/latest/) - Complete API reference

---

This guide provides everything needed to run efficient batch processing and automation workflows on the CANFAR Science Platform using headless containers.
