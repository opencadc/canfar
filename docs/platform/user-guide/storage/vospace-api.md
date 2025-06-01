# VOSpace API and Advanced Tools

Advanced data management capabilities using VOSpace APIs and command-line tools for automation and bulk operations.

## Overview

While the [Storage Guide](index.md) covers basic file operations, this guide focuses on programmatic access to your data using VOSpace APIs, command-line tools, and advanced workflows.

## VOSpace Command-Line Tools

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
export CADC_USERNAME=your_username
export CADC_PASSWORD=your_password
```

### Basic Operations

```bash
# List files and directories
vls vos:CANFAR/your_username/

# Copy files to VOSpace
vcp mydata.fits vos:CANFAR/your_username/data/

# Copy files from VOSpace  
vcp vos:CANFAR/your_username/data/mydata.fits ./

# Create directories
vmkdir vos:CANFAR/your_username/projects/survey_analysis/

# Move/rename files
vmv vos:CANFAR/your_username/old.fits vos:CANFAR/your_username/new.fits

# Remove files
vrm vos:CANFAR/your_username/temp/old_data.fits
```

### Bulk Operations

```bash
# Sync entire directories
vsync --recursive ./local_data/ vos:CANFAR/your_username/backup/

# Download project data
vsync --recursive vos:CANFAR/shared_project/survey_data/ ./project_data/

# Upload analysis results
vsync --recursive ./results/ vos:CANFAR/your_username/analysis_outputs/
```

## Python API

### Basic Usage

```python
import vos

# Initialize client
client = vos.Client()

# List directory contents
files = client.listdir('vos:CANFAR/your_username/')
print(files)

# Check if file exists
exists = client.isfile('vos:CANFAR/your_username/data.fits')

# Get file info
info = client.get_info('vos:CANFAR/your_username/data.fits')
print(f"Size: {info['size']} bytes")
print(f"Modified: {info['date']}")
```

### File Operations

```python
# Copy file to VOSpace
client.copy('mydata.fits', 'vos:CANFAR/your_username/data/mydata.fits')

# Copy file from VOSpace
client.copy('vos:CANFAR/your_username/data/results.txt', './results.txt')

# Create directory
client.mkdir('vos:CANFAR/your_username/new_project/')

# Delete file
client.delete('vos:CANFAR/your_username/temp/old_file.txt')
```

### Advanced Operations

```python
import os
from astropy.io import fits

def process_fits_files(vospace_dir, output_dir):
    """Process all FITS files in a VOSpace directory"""
    
    # List all FITS files
    files = client.listdir(vospace_dir)
    fits_files = [f for f in files if f.endswith('.fits')]
    
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
            
            # Upload to VOSpace
            client.copy(output_path, f"vos:CANFAR/your_username/processed/{fits_file}")
        
        # Clean up temporary file
        os.remove(local_path)

# Usage
process_fits_files('vos:CANFAR/your_username/raw_data', './processed/')
```

## Automation Workflows

### Batch Processing Script

```python
#!/usr/bin/env python3
"""
Automated data processing pipeline using VOSpace
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
        client.listdir('vos:CANFAR/')
        return client
    except Exception as e:
        logger.error(f"VOSpace authentication failed: {e}")
        sys.exit(1)

def sync_input_data(client, remote_dir, local_dir):
    """Download input data from VOSpace"""
    logger.info(f"Syncing {remote_dir} to {local_dir}")
    
    Path(local_dir).mkdir(parents=True, exist_ok=True)
    
    # Get list of files
    files = client.listdir(remote_dir)
    
    for file in files:
        if file.endswith(('.fits', '.txt', '.csv')):
            remote_path = f"{remote_dir}/{file}"
            local_path = f"{local_dir}/{file}"
            
            if not Path(local_path).exists():
                logger.info(f"Downloading {file}")
                client.copy(remote_path, local_path)

def upload_results(client, local_dir, remote_dir):
    """Upload processing results to VOSpace"""
    logger.info(f"Uploading results from {local_dir} to {remote_dir}")
    
    # Ensure remote directory exists
    try:
        client.mkdir(remote_dir)
    except:
        pass  # Directory might already exist
    
    for file_path in Path(local_dir).glob('*'):
        if file_path.is_file():
            remote_path = f"{remote_dir}/{file_path.name}"
            logger.info(f"Uploading {file_path.name}")
            client.copy(str(file_path), remote_path)

def main():
    """Main processing pipeline"""
    client = setup_vospace()
    
    # Configuration
    input_remote = 'vos:CANFAR/shared_project/raw_data'
    output_remote = 'vos:CANFAR/your_username/processed_results'
    local_input = './input_data'
    local_output = './output_data'
    
    # Download input data
    sync_input_data(client, input_remote, local_input)
    
    # Your processing code here
    logger.info("Processing data...")
    # ... processing logic ...
    
    # Upload results
    upload_results(client, local_output, output_remote)
    
    logger.info("Pipeline completed successfully")

if __name__ == '__main__':
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
    if source.startswith('vos:'):
        info = client.get_info(source)
        size_mb = info['size'] / (1024 * 1024)
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
                time.sleep(2 ** attempt)  # Exponential backoff
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
    remote_hash = remote_info.get('MD5', '')
    
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
    local_path = './temp_catalog.fits'
    client.copy(catalog_path, local_path)
    
    # Load and analyze
    table = Table.read(local_path)
    
    # Example analysis
    bright_sources = table[table['magnitude'] < 15]
    print(f"Found {len(bright_sources)} bright sources")
    
    # Save filtered results
    result_path = './bright_sources.fits'
    bright_sources.write(result_path, overwrite=True)
    
    # Upload results
    result_vospace = catalog_path.replace('.fits', '_bright.fits')
    client.copy(result_path, result_vospace)
    
    # Cleanup
    os.remove(local_path)
    os.remove(result_path)
```

### With Batch Jobs

```bash
#!/bin/bash
# Batch job script using VOSpace

# Authenticate
cadc-get-cert --cert ~/.ssl/cadcproxy.pem

# Download input data
vcp vos:CANFAR/project/input/data.fits ./input.fits

# Process data
python analysis_script.py input.fits output.fits

# Upload results
vcp output.fits vos:CANFAR/project/results/processed_$(date +%Y%m%d).fits

# Cleanup
rm input.fits output.fits
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
# Check file permissions
vls -l vos:CANFAR/your_username/file.fits

# Check directory access
vls vos:CANFAR/project_name/
```

## Next Steps

- **[Storage Guide →](index.md)** - Basic storage concepts and web interface
- **[Batch Jobs →](../batch-jobs/index.md)** - Automate VOSpace workflows
- **[Containers →](../containers/index.md)** - Include VOSpace tools in custom containers
- **[Radio Astronomy →](../radio-astronomy/index.md)** - Specialized data workflows
