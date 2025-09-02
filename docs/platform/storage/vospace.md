


# Vault (VOSpace API) and ARC Access

Advanced data management capabilities using the VOSpace API for Vault (archive storage, vos: URIs) and ARC (project/home storage, arc: URIs). Both can be accessed programmatically and via command-line tools for automation and bulk operations.


**ARC Access:**

- **Inside a CANFAR session:** Use standard Unix commands (`cp`, `ls`, etc.) for `/arc/projects/[projectname]` and `/arc/home/[username]`.
- **Outside a CANFAR session:** Use SSHFS to mount `/arc` or use VOSpace API with `arc:` URIs.


## Overview

While the [Storage Guide](index.md) covers basic file operations, this guide focuses on programmatic access to your data using the VOSpace API, command-line tools, and advanced workflows. You can access:

- **Vault**: Long-term archive storage via `vos:` URIs (e.g., `vos:[username]/` or `vos:[projectname]`)
- **ARC**: Project and home storage via `arc:` URIs (e.g., `arc:projects/[projectname]/mydatafile.fits`)



## Command-Line Tools



### Installation

VOSpace tools are pre-installed in all CANFAR containers. For local use:

```bash
# In CANFAR notebook/desktop session
pip install vos

# Verify installation
vls --help
```



### Authentication

```bash
# Get a security certificate (valid for 24 hours)
cadc-get-cert --cert ~/.ssl/cadcproxy.pem

# Or use your username/password
export CADC_USERNAME=[username]
export CADC_PASSWORD=[password]
```




### Basic Operations

#### Vault (VOSpace API)

```bash
# List files and directories in Vault
vls vos:[username]/

# Copy files to Vault
vcp mydata.fits vos:[username]/data/

# Copy files from Vault
vcp vos:[username]/data/mydata.fits ./

# Create directories in Vault
vmkdir vos:[username]/projects/survey_analysis/

# Move/rename files in Vault
vmv vos:[username]/old.fits vos:[username]/new.fits

# Remove files in Vault
vrm vos:[username]/temp/old_data.fits
```


#### ARC (VOSpace API, outside CANFAR)

```bash
# List files and directories in ARC
vls arc:projects/[projectname]/

# Copy files to ARC
vcp mydata.fits arc:projects/[projectname]/data/

# Copy files from ARC
vcp arc:projects/[projectname]/data/mydata.fits ./

# Create directories in ARC
vmkdir arc:projects/[projectname]/survey_analysis/

# Move/rename files in ARC
vmv arc:projects/[projectname]/old.fits arc:projects/[projectname]/new.fits

# Remove files in ARC
vrm arc:projects/[projectname]/temp/old_data.fits
```


#### ARC (Inside CANFAR session)

```bash
# List files and directories
ls /arc/projects/[projectname]/

# Copy files
cp mydata.fits /arc/projects/[projectname]/data/

# Create directories
mkdir /arc/projects/[projectname]/survey_analysis/

# Move/rename files
mv /arc/projects/[projectname]/old.fits /arc/projects/[projectname]/new.fits

# Remove files
rm /arc/projects/[projectname]/temp/old_data.fits
```



### Bulk Operations

> Note: `vsync` and `vcp` are always recursive; no `--recursive` flag is needed.


#### Vault (VOSpace API)

```bash
# Sync entire directories to Vault
vsync ./local_data/ vos:[username]/backup/

# Download project data from Vault
vsync vos:shared_project/survey_data/ ./project_data/

# Upload analysis results to Vault
vsync ./results/ vos:[username]/analysis_outputs/
```


#### ARC (VOSpace API, outside CANFAR)

```bash
# Sync entire directories to ARC
vsync ./local_data/ arc:projects/[projectname]/backup/

# Download project data from ARC
vsync arc:projects/[projectname]/survey_data/ ./project_data/

# Upload analysis results to ARC
vsync ./results/ arc:projects/[projectname]/analysis_outputs/
```



## Python API


### Basic Usage

```python
import vos

# Initialize client
client = vos.Client()


# List directory contents in Vault
files_vault = client.listdir("vos:[username]/")
print(files_vault)

# List directory contents in ARC
files_arc = client.listdir("arc:projects/[projectname]/")
print(files_arc)

# Check if file exists in Vault
exists_vault = client.isfile("vos:[username]/data.fits")

# Check if file exists in ARC
exists_arc = client.isfile("arc:projects/[projectname]/data.fits")

# Get file info from Vault
info_vault = client.get_info("vos:[username]/data.fits")
print(f"Size: {info_vault['size']} bytes")
print(f"Modified: {info_vault['date']}")

# Get file info from ARC
info_arc = client.get_info("arc:projects/[projectname]/data.fits")
print(f"Size: {info_arc['size']} bytes")
print(f"Modified: {info_arc['date']}")
```


### File Operations

```python

# Copy file to Vault
client.copy("mydata.fits", "vos:[username]/data/mydata.fits")

# Copy file to ARC
client.copy("mydata.fits", "arc:projects/[projectname]/data/mydata.fits")

# Copy file from Vault
client.copy("vos:[username]/data/results.txt", "./results.txt")

# Copy file from ARC
client.copy("arc:projects/[projectname]/data/results.txt", "./results.txt")

# Create directory in Vault
client.mkdir("vos:[username]/new_project/")

# Create directory in ARC
client.mkdir("arc:projects/[projectname]/new_project/")

# Delete file in Vault
client.delete("vos:[username]/temp/old_file.txt")

# Delete file in ARC
client.delete("arc:projects/[projectname]/temp/old_file.txt")
```


### Advanced Operations

```python
import os
from astropy.io import fits

def process_fits_files(vospace_dir, output_dir):
    """Process all FITS files in a Vault or ARC directory"""

    # List all FITS files
    files = client.listdir(vospace_dir)
    fits_files = [f for f in files if f.endswith(".fits")]

    for fits_file in fits_files:
        vospace_path = f"{vospace_dir}/{fits_file}"
        local_path = f"./temp_{fits_file}"

        # Download file
        client.copy(vospace_path, local_path)

        # Process with astropy
        with fits.open(local_path) as hdul:
            # Your processing here
            processed_data = hdul[0].data * 2  # Example processing

            # Save processed file
            output_path = f"{output_dir}/processed_{fits_file}"
            fits.writeto(output_path, processed_data, overwrite=True)


            # Upload to Vault or ARC
            if vospace_dir.startswith("vos:"):
                client.copy(output_path, f"vos:your_username/processed/{fits_file}")
            else:
                client.copy(output_path, f"arc:projects/myproject/processed/{fits_file}")

        # Clean up temporary file
        os.remove(local_path)

# Usage

process_fits_files("vos:your_username/raw_data", "./processed/")
process_fits_files("arc:projects/myproject/raw_data", "./processed/")
```


## Automation Workflows


### Batch Processing Script

```python
#!/usr/bin/env python3
"""
Automated data processing pipeline using Vault (VOSpace API) and ARC
"""
import vos
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_vospace():
    """Initialize VOSpace client with authentication"""
    try:
        client = vos.Client()
        # Test connection
        client.listdir("vos:CANFAR/")
        return client
    except Exception as e:
        logger.error(f"VOSpace authentication failed: {e}")
        sys.exit(1)

def sync_input_data(client, remote_dir, local_dir):
    """Download input data from Vault or ARC"""
    logger.info(f"Syncing {remote_dir} to {local_dir}")

    Path(local_dir).mkdir(parents=True, exist_ok=True)

    # Get list of files
    files = client.listdir(remote_dir)

    for file in files:
        if file.endswith((".fits", ".txt", ".csv")):
            remote_path = f"{remote_dir}/{file}"
            local_path = f"{local_dir}/{file}"

            if not Path(local_path).exists():
                logger.info(f"Downloading {file}")
                client.copy(remote_path, local_path)

def upload_results(client, local_dir, remote_dir):
    """Upload processing results to Vault or ARC"""
    logger.info(f"Uploading results from {local_dir} to {remote_dir}")

    # Ensure remote directory exists
    try:
        client.mkdir(remote_dir)
    except:
        pass  # Directory might already exist

    for file_path in Path(local_dir).glob("*"):
        if file_path.is_file():
            remote_path = f"{remote_dir}/{file_path.name}"
            logger.info(f"Uploading {file_path.name}")
            client.copy(str(file_path), remote_path)

def main():
    """Main processing pipeline"""
    client = setup_vospace()

    # Configuration
    input_remote_vault = "vos:shared_project/raw_data"
    input_remote_arc = "arc:projects/myproject/raw_data"
    output_remote_vault = "vos:your_username/processed_results"
    output_remote_arc = "arc:projects/myproject/processed_results"
    local_input = "./input_data"
    local_output = "./output_data"

    # Download input data from Vault
    sync_input_data(client, input_remote_vault, local_input)
    # Download input data from ARC
    sync_input_data(client, input_remote_arc, local_input)

    # Your processing code here
    logger.info("Processing data...")
    # ... processing logic ...

    # Upload results to Vault
    upload_results(client, local_output, output_remote_vault)
    # Upload results to ARC
    upload_results(client, local_output, output_remote_arc)

    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()
```

## Monitoring and Logging

### Transfer Progress

```python
def copy_with_progress(client, source, destination):
    """Copy file with progress monitoring"""
    import time

    # Start transfer
    start_time = time.time()
    client.copy(source, destination)
    end_time = time.time()

    # Get file size for speed calculation
    if source.startswith("vos:"):
        info = client.get_info(source)
        size_mb = info["size"] / (1024 * 1024)
    else:
        size_mb = os.path.getsize(source) / (1024 * 1024)

    duration = end_time - start_time
    speed = size_mb / duration if duration > 0 else 0

    print(f"Transfer completed: {size_mb:.1f} MB in {duration:.1f}s ({speed:.1f} MB/s)")
```

### Error Handling

```python
def robust_copy(client, source, destination, max_retries=3):
    """Copy with retry logic"""
    import time

    for attempt in range(max_retries):
        try:
            client.copy(source, destination)
            return True
        except Exception as e:
            logger.warning(f"Copy attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)  # Exponential backoff
            else:
                logger.error(f"Copy failed after {max_retries} attempts")
                return False
```

## Performance Optimization

### Parallel Transfers

```python
import concurrent.futures
import threading


def parallel_upload(client, file_list, remote_dir, max_workers=4):
    """Upload multiple files in parallel"""

    def upload_file(file_path):
        remote_path = f"{remote_dir}/{file_path.name}"
        try:
            client.copy(str(file_path), remote_path)
            return f"✓ {file_path.name}"
        except Exception as e:
            return f"✗ {file_path.name}: {e}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(upload_file, f) for f in file_list]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            print(result)
```

### Caching Strategy

```python
import hashlib
from pathlib import Path


def cached_download(client, vospace_path, local_path, force_refresh=False):
    """Download file only if it has changed"""

    local_file = Path(local_path)
    cache_file = Path(f"{local_path}.cache_info")

    # Get remote file info
    remote_info = client.get_info(vospace_path)
    remote_hash = remote_info.get("MD5", "")

    # Check if we have cached info
    if not force_refresh and local_file.exists() and cache_file.exists():
        cached_hash = cache_file.read_text().strip()
        if cached_hash == remote_hash:
            print(f"Using cached version of {local_file.name}")
            return local_path

    # Download file
    print(f"Downloading {local_file.name}")
    client.copy(vospace_path, local_path)

    # Save cache info
    cache_file.write_text(remote_hash)

    return local_path
```

## Integration Examples

### With Astropy

```python
from astropy.io import fits
from astropy.table import Table


def analyze_vospace_catalog(client, catalog_path):
    """Analyze a catalog stored in VOSpace"""

    # Download catalog
    local_path = "./temp_catalog.fits"
    client.copy(catalog_path, local_path)

    # Load and analyze
    table = Table.read(local_path)

    # Example analysis
    bright_sources = table[table["magnitude"] < 15]
    print(f"Found {len(bright_sources)} bright sources")

    # Save filtered results
    result_path = "./bright_sources.fits"
    bright_sources.write(result_path, overwrite=True)

    # Upload results
    result_vospace = catalog_path.replace(".fits", "_bright.fits")
    client.copy(result_path, result_vospace)

    # Cleanup
    os.remove(local_path)
    os.remove(result_path)
```


### With Batch Jobs

```bash
#!/bin/bash
# Batch job script using Vault and ARC via VOSpace API

# Authenticate
cadc-get-cert --cert ~/.ssl/cadcproxy.pem


# Download input data from Vault
vcp vos:project/input/data.fits ./input.fits
# Download input data from ARC
vcp arc:projects/myproject/input/data.fits ./input_arc.fits

# Process data
python analysis_script.py input.fits output.fits

# Upload results to Vault
vcp output.fits vos:project/results/processed_$(date +%Y%m%d).fits
# Upload results to ARC
vcp output.fits arc:projects/myproject/results/processed_$(date +%Y%m%d).fits

# Cleanup
rm input.fits input_arc.fits output.fits
```


## Troubleshooting

### Common Issues

**Authentication Problems:**
```bash
# Refresh certificate
cadc-get-cert --cert ~/.ssl/cadcproxy.pem

# Check certificate validity
cadc-get-cert --cert ~/.ssl/cadcproxy.pem --days-valid
```

**Network Timeouts:**
```python
# Increase timeout for large files
import vos

client = vos.Client()
client.timeout = 300  # 5 minutes
```


**Permission Errors:**
```bash

# Check file permissions in Vault
vls -l vos:your_username/file.fits
# Check file permissions in ARC
vls -l arc:projects/myproject/file.fits

# Check directory access in Vault
vls vos:project_name/
# Check directory access in ARC
vls arc:projects/myproject/
```

## Next Steps

- **[Batch Jobs →](../../batch-jobs.md)** - Automate VOSpace workflows
- **[Containers →](../../containers.md)** - Include VOSpace tools in custom containers
- **[Radio Astronomy →](../radio-astronomy/index.md)** - Specialized data workflows
