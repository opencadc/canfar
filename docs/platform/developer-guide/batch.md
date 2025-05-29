# Batch Processing and Headless Jobs

Guide to running non-interactive batch jobs and automated workflows on CANFAR.

## ⚡ Batch Processing Overview

**Batch processing** allows you to run computational jobs without interactive interfaces - perfect for:

- **Long-running analyses** that don't need user interaction
- **Automated pipelines** that process multiple datasets
- **Parameter sweeps** across different configurations
- **Background processing** while you work on other tasks

!!! warning "Limited Capacity"
    CANFAR has limited batch processing capacity. **Contact [support@canfar.net](mailto:support@canfar.net) before starting batch work** to discuss your requirements and get approval.

---

## 🚀 Quick Start

### 1. Prepare Your Script
```python
#!/usr/bin/env python3
# process_data.py

import sys
import os
from astropy.io import fits
import numpy as np

def main():
    if len(sys.argv) != 3:
        print("Usage: python process_data.py input_file output_file")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Your analysis code here
    data = fits.getdata(input_file)
    processed = np.median(data, axis=0)  # Example processing
    
    # Save results
    fits.writeto(output_file, processed, overwrite=True)
    print(f"Processed {input_file} -> {output_file}")

if __name__ == "__main__":
    main()
```

### 2. Launch Headless Job
```bash
# Using curl (from terminal)
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "name=data-processing-job" \
  -d "image=images.canfar.net/skaha/astroconda:latest" \
  -d "cores=4" \
  -d "ram=8" \
  -d "kind=headless" \
  -d "cmd=python /arc/projects/mygroup/scripts/process_data.py /arc/projects/mygroup/data/input.fits /arc/projects/mygroup/results/output.fits" \
  https://ws-uv.canfar.net/skaha/v0/session
```

### 3. Monitor Job Status
```bash
# Check job status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://ws-uv.canfar.net/skaha/v0/session/SESSION_ID
```

---

## 🔄 Common Batch Workflows

### 1. Single File Processing

```python
# launch_single_job.py
import requests
import sys

def launch_processing_job(input_file, output_file, token):
    headers = {"Authorization": f"Bearer {token}"}
    
    job_data = {
        "name": f"process-{os.path.basename(input_file)}",
        "image": "images.canfar.net/skaha/astroconda:latest",
        "cores": 2,
        "ram": 4,
        "kind": "headless",
        "cmd": f"python /arc/projects/mygroup/scripts/process_data.py {input_file} {output_file}"
    }
    
    response = requests.post("https://ws-uv.canfar.net/skaha/v0/session",
                           headers=headers, data=job_data)
    
    if response.status_code == 200:
        session_id = response.json()['sessionId']
        print(f"Job launched: {session_id}")
        return session_id
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Usage
token = "your_api_token"
job_id = launch_processing_job(
    "/arc/projects/mygroup/data/observation1.fits",
    "/arc/projects/mygroup/results/processed1.fits",
    token
)
```

### 2. Parallel Processing of Multiple Files

```python
# parallel_batch.py
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor

def launch_job(file_info, token):
    """Launch a single batch job"""
    input_file, output_file = file_info
    headers = {"Authorization": f"Bearer {token}"}
    
    job_data = {
        "name": f"batch-{os.path.basename(input_file).replace('.fits', '')}",
        "image": "images.canfar.net/skaha/astroconda:latest",
        "cores": 2,
        "ram": 4,
        "kind": "headless",
        "cmd": f"python /arc/projects/mygroup/scripts/process_data.py {input_file} {output_file}"
    }
    
    response = requests.post("https://ws-uv.canfar.net/skaha/v0/session",
                           headers=headers, data=job_data)
    
    if response.status_code == 200:
        return response.json()['sessionId']
    else:
        print(f"Failed to launch job for {input_file}: {response.text}")
        return None

def batch_process_files(input_files, output_dir, token, max_concurrent=3):
    """Process multiple files in parallel batches"""
    
    # Create file pairs
    file_pairs = []
    for input_file in input_files:
        filename = os.path.basename(input_file)
        output_file = os.path.join(output_dir, f"processed_{filename}")
        file_pairs.append((input_file, output_file))
    
    # Launch jobs in batches to respect session limits
    session_ids = []
    
    # Process in chunks to avoid hitting session limits
    chunk_size = max_concurrent
    for i in range(0, len(file_pairs), chunk_size):
        chunk = file_pairs[i:i + chunk_size]
        
        # Launch jobs for this chunk
        with ThreadPoolExecutor(max_workers=chunk_size) as executor:
            futures = [executor.submit(launch_job, pair, token) for pair in chunk]
            chunk_sessions = [f.result() for f in futures if f.result()]
        
        session_ids.extend(chunk_sessions)
        print(f"Launched {len(chunk_sessions)} jobs (batch {i//chunk_size + 1})")
        
        # Wait for this batch to complete before starting next
        if i + chunk_size < len(file_pairs):
            wait_for_completion(chunk_sessions, token)
            time.sleep(30)  # Brief pause between batches
    
    return session_ids

# Usage
input_files = [
    "/arc/projects/mygroup/data/obs1.fits",
    "/arc/projects/mygroup/data/obs2.fits", 
    "/arc/projects/mygroup/data/obs3.fits"
]

session_ids = batch_process_files(
    input_files,
    "/arc/projects/mygroup/results/",
    "your_api_token"
)
```

### 3. Parameter Sweep Jobs

```python
# parameter_sweep.py
import itertools
import requests

def launch_parameter_sweep(param_combinations, script_path, token):
    """Launch jobs for different parameter combinations"""
    
    session_ids = []
    headers = {"Authorization": f"Bearer {token}"}
    
    for i, params in enumerate(param_combinations):
        # Convert parameters to command line arguments
        param_args = " ".join([f"--{k} {v}" for k, v in params.items()])
        
        job_data = {
            "name": f"param-sweep-{i:03d}",
            "image": "images.canfar.net/skaha/astroconda:latest",
            "cores": 2,
            "ram": 4,
            "kind": "headless",
            "cmd": f"python {script_path} {param_args}"
        }
        
        response = requests.post("https://ws-uv.canfar.net/skaha/v0/session",
                               headers=headers, data=job_data)
        
        if response.status_code == 200:
            session_id = response.json()['sessionId']
            session_ids.append(session_id)
            print(f"Launched parameter job {i}: {session_id}")
        else:
            print(f"Failed to launch job {i}: {response.text}")
    
    return session_ids

# Define parameter grid
param_grid = {
    'threshold': [0.1, 0.5, 1.0],
    'sigma': [1.0, 2.0, 3.0],
    'method': ['gaussian', 'tophat']
}

# Generate all combinations
param_combinations = [
    dict(zip(param_grid.keys(), values))
    for values in itertools.product(*param_grid.values())
]

# Launch sweep
session_ids = launch_parameter_sweep(
    param_combinations,
    "/arc/projects/mygroup/scripts/analysis_with_params.py",
    "your_api_token"
)
```

---

## 📊 Job Monitoring and Management

### Monitor Job Progress

```python
# monitor_jobs.py
import requests
import time
import json

def monitor_batch_jobs(session_ids, token, check_interval=60):
    """Monitor multiple batch jobs until completion"""
    
    headers = {"Authorization": f"Bearer {token}"}
    active_jobs = session_ids.copy()
    completed_jobs = []
    failed_jobs = []
    
    print(f"Monitoring {len(active_jobs)} batch jobs...")
    
    while active_jobs:
        current_status = {}
        
        for session_id in active_jobs[:]:  # Copy list to allow modification
            try:
                response = requests.get(
                    f"https://ws-uv.canfar.net/skaha/v0/session/{session_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    session_info = response.json()
                    status = session_info.get('status', 'Unknown')
                    current_status[session_id] = status
                    
                    if status in ['Succeeded', 'Terminating']:
                        completed_jobs.append(session_id)
                        active_jobs.remove(session_id)
                        print(f"✅ Job {session_id}: Completed")
                        
                    elif status == 'Error':
                        failed_jobs.append(session_id)
                        active_jobs.remove(session_id)
                        error_msg = session_info.get('statusMessage', 'Unknown error')
                        print(f"❌ Job {session_id}: Failed - {error_msg}")
                        
                elif response.status_code == 404:
                    # Job no longer exists (likely completed)
                    completed_jobs.append(session_id)
                    active_jobs.remove(session_id)
                    print(f"✅ Job {session_id}: Completed (no longer in system)")
                    
            except Exception as e:
                print(f"⚠️  Error checking job {session_id}: {e}")
        
        # Print status summary
        if active_jobs:
            status_counts = {}
            for status in current_status.values():
                status_counts[status] = status_counts.get(status, 0) + 1
            
            status_str = ", ".join([f"{k}: {v}" for k, v in status_counts.items()])
            print(f"Status update: {status_str}")
            time.sleep(check_interval)
    
    print(f"\n🎉 All jobs completed!")
    print(f"✅ Successful: {len(completed_jobs)}")
    print(f"❌ Failed: {len(failed_jobs)}")
    
    return completed_jobs, failed_jobs

# Usage
completed, failed = monitor_batch_jobs(session_ids, "your_api_token")
```

### Collect Job Results

```python
# collect_results.py
import os
import glob

def collect_batch_results(output_directory, result_pattern="processed_*.fits"):
    """Collect and summarize results from batch jobs"""
    
    result_files = glob.glob(os.path.join(output_directory, result_pattern))
    
    print(f"Found {len(result_files)} result files:")
    for file_path in sorted(result_files):
        file_size = os.path.getsize(file_path) / (1024*1024)  # MB
        print(f"  {os.path.basename(file_path)}: {file_size:.1f} MB")
    
    return result_files

# Collect results
results = collect_batch_results("/arc/projects/mygroup/results/")
```

---

## 🛠️ Best Practices

### Script Design

```python
# robust_batch_script.py
import sys
import os
import logging
import traceback
from datetime import datetime

def setup_logging(log_file):
    """Setup logging for batch job"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def main():
    # Setup
    job_id = os.environ.get('SKAHA_SESSION_ID', 'unknown')
    log_file = f"/arc/projects/mygroup/logs/job_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    setup_logging(log_file)
    
    try:
        logging.info(f"Starting batch job {job_id}")
        logging.info(f"Arguments: {sys.argv}")
        
        # Your processing code here
        process_data()
        
        logging.info("Job completed successfully")
        return 0
        
    except Exception as e:
        logging.error(f"Job failed with error: {e}")
        logging.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
```

### Resource Management

```python
# Check available resources before launching
def check_resource_availability(token):
    """Check current resource usage before launching batch jobs"""
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://ws-uv.canfar.net/skaha/v0/session", headers=headers)
    
    if response.status_code == 200:
        sessions = response.json()
        
        total_cores = sum(s.get('cores', 0) for s in sessions)
        total_ram = sum(s.get('ram', 0) for s in sessions)
        active_count = len(sessions)
        
        print(f"Current usage:")
        print(f"  Active sessions: {active_count}/3")
        print(f"  Total cores: {total_cores}")
        print(f"  Total RAM: {total_ram} GB")
        
        return active_count < 3  # Can launch more jobs
    
    return False
```

### Error Handling

```python
def robust_job_launcher(job_config, token, max_retries=3):
    """Launch job with retry logic and error handling"""
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for attempt in range(max_retries):
        try:
            # Check if we can launch more jobs
            if not check_resource_availability(token):
                print("Resource limit reached, waiting...")
                time.sleep(60)
                continue
            
            response = requests.post(
                "https://ws-uv.canfar.net/skaha/v0/session",
                headers=headers,
                data=job_config,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['sessionId']
            elif response.status_code == 409:
                print(f"Conflict (attempt {attempt + 1}): Resource busy")
                time.sleep(30)
            else:
                print(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error (attempt {attempt + 1}): {e}")
            time.sleep(30)
    
    raise Exception(f"Failed to launch job after {max_retries} attempts")
```

---

## 📋 Job Templates

### Basic Processing Template

```bash
#!/bin/bash
# batch_template.sh

# Job configuration
export JOB_NAME="data-processing"
export INPUT_DIR="/arc/projects/mygroup/data"
export OUTPUT_DIR="/arc/projects/mygroup/results"
export SCRIPT_PATH="/arc/projects/mygroup/scripts/process.py"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Run processing
python "${SCRIPT_PATH}" \
  --input-dir "${INPUT_DIR}" \
  --output-dir "${OUTPUT_DIR}" \
  --job-id "${SKAHA_SESSION_ID:-unknown}"

echo "Job completed: $(date)"
```

### Machine Learning Training Template

```python
#!/usr/bin/env python3
# ml_training_job.py

import os
import sys
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

def main():
    # Configuration from environment or arguments
    data_path = sys.argv[1] if len(sys.argv) > 1 else "/arc/projects/mygroup/data/training_data.npy"
    model_output = sys.argv[2] if len(sys.argv) > 2 else "/arc/projects/mygroup/models/trained_model.pkl"
    
    # Load data
    print(f"Loading data from {data_path}")
    data = np.load(data_path)
    X, y = data['features'], data['labels']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    print("Training model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"Training accuracy: {train_score:.3f}")
    print(f"Testing accuracy: {test_score:.3f}")
    
    # Save model
    os.makedirs(os.path.dirname(model_output), exist_ok=True)
    joblib.dump(model, model_output)
    print(f"Model saved to {model_output}")

if __name__ == "__main__":
    main()
```

---

## 🔍 Troubleshooting

### Common Issues

**Jobs Stuck in Pending**
- Check resource limits (3 session maximum)
- Verify container image access permissions
- Contact support if image appears broken

**Jobs Failing Immediately**
- Check script syntax and permissions
- Verify input file paths exist
- Review container environment requirements

**Slow Job Performance**
- Monitor resource usage in job logs
- Consider optimizing I/O patterns
- Use appropriate number of cores for workload

**Out of Storage Space**
- Clean up temporary files in scripts
- Use `/tmp` for intermediate processing
- Monitor disk usage during jobs

### Debugging Tips

```python
# Add debugging info to batch scripts
import psutil
import os

print(f"Job started on: {os.uname().nodename}")
print(f"Available memory: {psutil.virtual_memory().available / 1e9:.1f} GB")
print(f"CPU count: {psutil.cpu_count()}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment variables:")
for key, value in sorted(os.environ.items()):
    if key.startswith('SKAHA') or key in ['USER', 'HOME', 'PATH']:
        print(f"  {key}: {value}")
```

---

## 🆘 Getting Help

### Before Contacting Support
1. **Check session limits**: Are you at the 3-session maximum?
2. **Verify file paths**: Do input files exist and are accessible?
3. **Test interactively**: Run your script in a notebook first
4. **Check logs**: Look for error messages in job output

### Contact Information
- **Batch processing approval**: [support@canfar.net](mailto:support@canfar.net)
- **Technical issues**: [Slack channel](https://cadc.slack.com/archives/C01K60U5Q87)
- **Resource requests**: Include project details and expected usage

### What to Include in Support Requests
- Session ID of failed job
- Full error messages or logs
- Script/command you're trying to run
- Expected vs. actual behavior
- Project and resource requirements
