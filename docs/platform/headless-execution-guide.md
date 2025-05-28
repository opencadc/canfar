# Headless Container Execution Guide

This guide covers how to run headless containers on the CANFAR Science Platform using both curl commands and the skaha Python client for batch processing and automation.

## Overview

Headless containers are designed for:
- **Batch Processing**: Large-scale data analysis without user interaction
- **Automation**: Scheduled or triggered processing workflows  
- **Command-Line Tools**: Running CLI applications remotely
- **API Integration**: Programmatic job submission and monitoring

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
   - Login to https://images.canfar.net
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

## Best Practices

### Job Design
- **Stateless**: Design jobs to be independent and repeatable
- **Idempotent**: Jobs should produce same results if re-run
- **Error Handling**: Include proper error checking and logging
- **Resource Estimates**: Request appropriate CPU/memory resources

### Data Management
- **Input Validation**: Check input files exist before processing
- **Output Organization**: Use consistent naming and directory structure
- **Intermediate Files**: Clean up temporary files to save space
- **Logging**: Write detailed logs for debugging

### Performance
- **Parallel Processing**: Use multiple cores when available
- **I/O Optimization**: Minimize unnecessary file operations
- **Memory Management**: Monitor memory usage in long-running jobs
- **Batch Size**: Optimize number of files processed per job

### Security
- **Credentials**: Never hardcode secrets in containers
- **File Permissions**: Ensure proper access controls
- **Registry Access**: Keep CLI secrets secure and rotate regularly

## Troubleshooting

### Common Issues

#### Job Stuck in Pending
```bash
# Check scheduling events for details
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session/${SESSION_ID}?view=events
```

Common causes:
- Expired CLI secret for private images
- Insufficient cluster resources
- Invalid image reference
- Missing project permissions

#### Job Failed
```bash
# Check job logs for error messages
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session/${SESSION_ID}?view=logs
```

Common causes:
- Command not found in container
- File path errors
- Permission issues
- Resource limits exceeded

### Debugging Tips

1. **Test Locally First**: 
   ```bash
   docker run -it your-image:tag /bin/bash
   # Test your command interactively
   ```

2. **Start Simple**:
   ```bash
   # Test with basic command first
   curl -E ~/.ssl/cadcproxy.pem \
     https://ws-uv.canfar.net/skaha/v0/session \
     -d "name=test" \
     -d "image=your-image" \
     -d "kind=headless" \
     --data-urlencode "cmd=echo" \
     --data-urlencode "args=Hello World"
   ```

3. **Check Container Logs**:
   ```bash
   # View detailed output and error messages
   curl -E ~/.ssl/cadcproxy.pem \
     https://ws-uv.canfar.net/skaha/v0/session/${SESSION_ID}?view=logs
   ```

This guide provides comprehensive coverage of headless container execution on the CANFAR Science Platform. Use curl for simple job submission and monitoring, or the Python client for complex workflows and automation.
