# VOSpace

!!! abstract "🎯 VOSpace Guide Overview"
    **Master CANFAR's long-term storage system:**
    
    - **VOSpace Concepts**: Understanding IVOA standards and when to use Vault
    - **Web Interface**: Browser-based file management and sharing
    - **Command-Line Tools**: Efficient bulk operations and automation
    - **Python API**: Programmatic access for workflows and integration
    - **Metadata & Sharing**: Rich data descriptions and collaborative access

VOSpace is CANFAR's implementation of the International Virtual Observatory Alliance (IVOA) VOSpace standard, providing long-term, secure, and collaborative storage for astronomy data. It serves as both an archive and a data sharing platform.

## 🌐 VOSpace Overview

### What is VOSpace?

VOSpace is a distributed storage service that allows astronomers to:

- **Store data persistently** with geographic redundancy
- **Share data** with collaborators and the public
- **Organize data** with hierarchical directories and metadata
- **Access data** programmatically via standardized APIs
- **Integrate** with Virtual Observatory tools and services

### Vault VOSpace vs ARC VOSpace vs Scratch

| Feature | Vault | ARC Projects | ARC Home | Scratch |
|---------|-----------------|--------------|----------|---------|
| **Persistence** | ✅ Permanent | ✅ Permanent | ✅ Permanent | ❌ Session only |
| **Backup** | ✅ Geo-redundant | ⚠️ Basic | ⚠️ Basic | ❌ None |
| **Sharing** | ✅ Flexible permissions | ⚠️ Group-based |  ⚠️ User-based | ❌ Session only |
| **Public access** | ✅ Public URLs | ❌ Private | ❌ Private | ❌ Session only |
| **Metadata** | ✅ Rich metadata | ⚠️ Basic | ⚠️ Basic | ❌ None |
| **API access** | ✅ VOSpace API | ✅ VOSpace API | ✅ VOSpace API | ❌ None |
| **Speed** | Slow (network) | Medium (network) | Medium (network) | Fast (SSD) |

## 🌍 Web Interface

### Accessing VOSpace

1. **Navigate to**:
    - [Vault VOSpace File Manager](https://www.canfar.net/storage/vault/list/)
    - [ARC VOSpace File Manager](https://www.canfar.net/storage/arc/list/)
2. **Login**: Use your CADC credentials
3. **Browse**: Navigate through your space and shared spaces

### Web Interface Features

#### File Operations

- **Upload**: Drag and drop or click "Add" → "Upload Files"
- **Download**: Select files → "Download" (ZIP, URL list, or HTML list)
- **Create folders**: "Add" → "Create Folder"
- **Delete**: Select items → "Delete"
- **Move/Copy**: Drag and drop or cut/paste

#### Sharing and Permissions

```text
Right-click file/folder → Properties → Permissions

Permission Types:
- Read (r): View and download
- Write (w): Modify and delete  
- Execute (x): Navigate directories

Target Groups:
- Owner: You (full control)
- Group: Project members
- Other: Public access
```

## 💻 Command Line Interface

### Installation

VOSpace tools are pre-installed in CANFAR sessions in CANFAR-maintained containers such as `astroml`. 
For local or custom installation, use `pip`:

```bash
# Install VOS python module with vcp/vsync/vls/vchmod/vmkdir commands
pip install vos

# Verify installation
vls --help
vcp --help
```

### Authentication

```bash
# Get security certificate (valid 24 hours)
cadc-get-cert -u [user]

# Verify authentication
vls vos:[user]
```

### Basic Operations

#### Directory Operations

```bash
# List directories and files
vls vos:[user]/                    # Your root directory
vls vos:[user]/projects/           # Subdirectory
vls -l vos:[user]/data/            # Detailed listing

# Create directories
vmkdir vos:[user]/new_project/
vmkdir vos:[user]/data/2024/

# Navigate hierarchically
vls vos:[user]/projects/survey/data/
```

#### File Operations

```bash
# Upload files
vcp mydata.fits vos:[user]/data/
vcp *.fits vos:[user]/observations/
# vcp is recursive
vcp ./analysis_scripts/ vos:[user]/code/ 

# Download files  
vcp vos:[user]/data/results.fits ./
vcp "vos:[user]/observations/*.fits" ./data/
vcp vos:[user]/code/ ./local_scripts/

# Copy between VOSpace locations
vcp vos:[user]/data/obs1.fits vos:[user]/backup/
```

#### File Management

```bash
# Move/rename files
vmv vos:[user]/old_name.fits vos:[user]/new_name.fits
vmv vos:[user]/temp/ vos:[user]/archive/

# Delete files and directories
vrm vos:[user]/old_file.fits
vrm vos:[user]/old_directory/

# View file contents (for text files)
vcat vos:[user]/catalog.csv
```

### Advanced Operations

#### Bulk Operations

```bash
# Synchronise directories
vsync ./local_data/ vos:[user]/backup/
vsync vos:[user]/analysis/ ./local_analysis/

# Parallel transfers for speed
vsync --nstreams=4 huge_dataset.tar vos:[user]/archives/
```

#### Permission Management

```bash
# Make file publicly readable
vchmod o+r vos:[user]/public_catalog.fits

# Grant group access
vchmod g+rw vos:[user]/shared_data.fits

# Set permissions for specific groups
vchmod g+r:external-collaborators vos:[user]/collaboration_data/

# View current permissions
vls -l vos:[user]/myfile.fits
```

### Data Cutouts and Processing

```bash
# FITS cutouts (pixel coordinates)
vcp "vos:[user]/image.fits[100:200,100:200]" ./cutout.fits

# Header-only download
vcp --head vos:[user]/large_image.fits ./headers.txt

# Inspect headers without downloading
vcat --head vos:[user]/observation.fits

```

## 🐍 Python API

### Basic Setup

```python
import vos
from vos import Client

# Initialize client (uses existing authentication)
client = Client()

# Alternative: specify authentication
client = Client(username='[user]', password='[password]')
```

### File Operations

```python
# List directory contents
files = client.listdir('vos:[user]/')
print(f"Found {len(files)} files")

# Check if file exists
exists = client.isfile('vos:[user]/data.fits')
if not exists:
    print("File not found")

# Get file information
info = client.get_info('vos:[user]/data.fits')
print(f"Size: {info['size']} bytes")
print(f"Modified: {info['date']}")

# Copy files
client.copy('mydata.fits', 'vos:[user]/uploads/mydata.fits')
client.copy('vos:[user]/results.txt', './local_results.txt')

# Create directories
client.mkdir('vos:[user]/new_project/')

# Delete files
client.delete('vos:[user]/old_file.fits')
```

### Advanced Python Usage

#### Batch Processing

```python
import os
from pathlib import Path

def process_vospace_directory(vospace_path, local_temp_dir):
    """Download, process, and re-upload files from VOSpace"""
    
    # Create local working directory
    Path(local_temp_dir).mkdir(exist_ok=True)
    
    # List files in VOSpace
    files = client.listdir(vospace_path)
    fits_files = [f for f in files if f.endswith('.fits')]
    
    for fits_file in fits_files:
        vospace_file = f"{vospace_path}/{fits_file}"
        local_file = f"{local_temp_dir}/{fits_file}"
        processed_file = f"{local_temp_dir}/processed_{fits_file}"
        
        # Download
        print(f"Downloading {fits_file}")
        client.copy(vospace_file, local_file)
        
        # Process (example: your analysis here)
        process_fits_file(local_file, processed_file)
        
        # Upload processed version
        processed_vospace = f"{vospace_path}/processed_{fits_file}"
        client.copy(processed_file, processed_vospace)
        
        # Cleanup local files
        os.remove(local_file)
        os.remove(processed_file)

# Usage
process_vospace_directory('vos:[user]/raw_data', './temp_processing')
```

#### Metadata Management

```python
# Get file node (for metadata operations)
node = client.get_node('vos:[user]/observation.fits')

# Set metadata
node.props['TELESCOPE'] = 'ALMA'
node.props['OBJECT'] = 'NGC1365'
node.props['DATE-OBS'] = '2024-03-15T10:30:00'

# Update node with new metadata
client.update(node)

# Read metadata
props = node.props
telescope = props.get('TELESCOPE', 'Unknown')
object_name = props.get('OBJECT', 'Unknown')

print(f"Observation of {object_name} with {telescope}")
```

#### Progress Monitoring

```python
def upload_with_progress(local_file, vospace_path):
    """Upload file with progress monitoring"""
    
    file_size = os.path.getsize(local_file)
    
    def progress_callback(bytes_transferred):
        percent = (bytes_transferred / file_size) * 100
        print(f"\rProgress: {percent:.1f}% ({bytes_transferred}/{file_size} bytes)", end='')
    
    try:
        client.copy(local_file, vospace_path, callback=progress_callback)
        print("\nUpload completed successfully!")
    except Exception as e:
        print(f"\nUpload failed: {e}")

# Usage
upload_with_progress('large_dataset.fits', 'vos:[user]/archives/dataset.fits')
```

## 🔒 Sharing and Collaboration

### Permission Levels

#### Owner Permissions
- **Full control**: Read, write, delete, change permissions
- **Default**: Only owner has access to new files

#### Group Permissions  
- **Read**: Group members can view and download
- **Write**: Group members can modify and upload
- **Execute**: Group members can navigate directories

#### Public Permissions
- **Read**: Anyone with the URL can download
- **Useful for**: Publishing datasets, sharing with external collaborators

### Setting Up Sharing

#### Command Line Sharing

```bash
# Make dataset publicly available
vchmod o+r vos:[user]/public_datasets/gaia_subset.fits

# Share with research group
vchmod g+rw:my_research_group vos:[user]/shared_analysis/

# Create public directory
vmkdir vos:[user]/public/
vchmod o+r vos:[user]/public/

# Share specific project data
vchmod g+r:external_collaborators vos:[user]/collaboration/survey_data/
```

#### Public URLs

```bash
# Files with public read permissions get accessible URLs:
# https://ws-cadc.canfar.net/vault/nodes/[user]/public_file.fits

# Direct download links for shared data:
curl -O https://ws-cadc.canfar.net/vault/nodes/[user]/public/catalog.csv
```

### Collaboration Workflows

#### Multi-Institutional Project

```bash
# Project coordinator sets up shared space
vmkdir vos:[project]/data
vmkdir vos:[project]/public
vmkdir vos:[project]/results
vchmod g+rw:all_collaborators vos:[project]/data/

# Collaborators contribute data
vcp local_observations.fits vos:[project]/data/institution_a/
vcp analysis_results.csv vos:[project]/results/

# Public data release
vcp vos:[project]/data/final_catalogue.fits vos:[project]/public/
vchmod o+r vos:[project]/public/final_catalogue.fits
```

#### Data Publication

```python
import vos

def publish_dataset(local_files, publication_space):
    """Publish dataset with proper metadata"""
    
    client = vos.Client()
    
    # Create publication directory
    client.mkdir(publication_space)
    
    for local_file in local_files:
        filename = os.path.basename(local_file)
        vospace_path = f"{publication_space}/{filename}"
        
        # Upload file
        client.copy(local_file, vospace_path)
        
        # Set metadata
        node = client.get_node(vospace_path)
        node.props['AUTHOR'] = 'Dr. Astronomer'
        node.props['PUBLICATION'] = 'ApJ 2024, 123, 456'
        node.props['DOI'] = '10.1088/example'
        client.update(node)
        
        # Make publicly accessible
        client.set_permissions(vospace_path, public_read=True)
        
        print(f"Published: {vospace_path}")

# Usage
files_to_publish = ['final_catalog.fits', 'processed_images.tar.gz']
publish_dataset(files_to_publish, 'vos:[user]/publications/survey2024')
```

## 🔧 Integration with Astronomical Tools

### FITS File Handling

```python
from astropy.io import fits
import tempfile
import os

def analyze_vospace_fits(vospace_path):
    """Analyze FITS file stored in VOSpace"""
    
    # Download to temporary file
    with tempfile.NamedTemporaryFile(suffix='.fits', delete=False) as tmp:
        client.copy(vospace_path, tmp.name)
        
        # Open with astropy
        with fits.open(tmp.name) as hdul:
            header = hdul[0].header
            data = hdul[0].data
            
            # Perform analysis
            mean_value = data.mean()
            max_value = data.max()
            
            print(f"Image stats: mean={mean_value:.2f}, max={max_value:.2f}")
            
            # Extract key information
            telescope = header.get('TELESCOP', 'Unknown')
            object_name = header.get('OBJECT', 'Unknown')
            
        # Cleanup
        os.unlink(tmp.name)
        
    return {'mean': mean_value, 'max': max_value, 'telescope': telescope}

# Usage
stats = analyze_vospace_fits('vos:[user]/observations/ngc1365.fits')
```

### Integration with Archives

```python
def mirror_archive_data(archive_url, vospace_destination):
    """Download from astronomical archive and store in VOSpace"""
    
    import requests
    import tempfile
    
    # Download from archive
    response = requests.get(archive_url)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name
    
    try:
        # Upload to VOSpace
        client.copy(tmp_path, vospace_destination)
        
        # Set metadata about source
        node = client.get_node(vospace_destination)
        node.props['ARCHIVE_URL'] = archive_url
        node.props['DOWNLOAD_DATE'] = datetime.now().isoformat()
        client.update(node)
        
        print(f"Mirrored {archive_url} to {vospace_destination}")
        
    finally:
        os.unlink(tmp_path)

# Example: Mirror HST data
mirror_archive_data(
    'https://archive.stsci.edu/missions/hubble/...',
    'vos:[user]/hst_data/observation_123.fits'
)
```

## 📊 Performance and Optimization

### Transfer Performance


#### Caching and Local Mirrors

```python
import hashlib
from pathlib import Path

class VOSpaceCache:
    def __init__(self, cache_dir='./vospace_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.client = vos.Client()
    
    def get_cached_file(self, vospace_path, force_refresh=False):
        """Get file from cache or download if needed"""
        
        # Generate cache filename
        cache_name = hashlib.md5(vospace_path.encode()).hexdigest()
        cache_file = self.cache_dir / cache_name
        
        # Check if cache is valid
        if not force_refresh and cache_file.exists():
            # Compare modification times
            local_mtime = cache_file.stat().st_mtime
            try:
                remote_info = self.client.get_info(vospace_path)
                remote_mtime = remote_info['date']
                
                if local_mtime >= remote_mtime:
                    print(f"Using cached version: {cache_file}")
                    return str(cache_file)
            except:
                pass
        
        # Download fresh copy
        print(f"Downloading {vospace_path} to cache")
        self.client.copy(vospace_path, str(cache_file))
        return str(cache_file)

# Usage
cache = VOSpaceCache()
local_file = cache.get_cached_file('vos:[user]/large_catalog.fits')
```

### Monitoring and Logging

```python
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitored_transfer(source, destination):
    """Transfer with monitoring and timing"""
    
    start_time = time.time()
    logger.info(f"Starting transfer: {source} → {destination}")
    
    try:
        client.copy(source, destination)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Get file size for speed calculation
        if source.startswith('vos:'):
            info = client.get_info(source)
            size_mb = info['size'] / (1024 * 1024)
        else:
            size_mb = os.path.getsize(source) / (1024 * 1024)
        
        speed = size_mb / duration if duration > 0 else 0
        
        logger.info(f"Transfer completed: {size_mb:.1f} MB in {duration:.1f}s ({speed:.1f} MB/s)")
        return True
        
    except Exception as e:
        logger.error(f"Transfer failed: {e}")
        return False

# Usage
success = monitored_transfer('large_file.fits', 'vos:[user]/archives/')
```

## 🛠️ Troubleshooting

### Common Issues

#### Authentication Problems

```bash
# Certificate expired
cadc-get-cert -u [user]

# Check certificate validity
cadc-get-cert --days-valid

# Clear certificate cache
rm ~/.ssl/cadcproxy.pem
cadc-get-cert -u [user]
```

#### Permission Errors

```bash
# Check file permissions
vls -l vos:[user]/file.fits

# Verify directory permissions
vls -l vos:[user]/

# Check group membership
# (Contact CANFAR support if needed)
```

#### Network and Transfer Issues

```bash
# Test connectivity
ping ws-cadc.canfar.net

# Check VOSpace service status
vls vos:

# Retry with different parameters
vcp --timeout=3600 large_file.fits vos:[user]/  # Increase timeout
vcp --nstreams=1 problematic_file.fits vos:[user]/  # Reduce streams
```

### Debugging and Diagnostics

```python
import vos
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Get detailed client information
client = vos.Client()
print(f"VOSpace endpoint: {client.vospace_url}")
print(f"Authentication: {client.get_auth()}")

# Test basic operations
try:
    files = client.listdir('vos:')
    print(f"Root access successful, found {len(files)} items")
except Exception as e:
    print(f"Root access failed: {e}")

# Check specific paths
test_paths = ['vos:[user]/', 'vos:[user]/data/']
for path in test_paths:
    try:
        contents = client.listdir(path)
        print(f"✓ {path}: {len(contents)} items")
    except Exception as e:
        print(f"✗ {path}: {e}")
```

## 🔗 Next Steps

- **[Data Transfers →](transfers.md)** - Moving data between storage systems
- **[Filesystem Access →](filesystem.md)** - ARC storage and SSHFS mounting
- **[Storage Overview →](index.md)** - Understanding all CANFAR storage types
- **[Interactive Sessions →](../sessions/index.md)** - Using VOSpace within CANFAR sessions
```


#### ARC (Inside CANFAR session)

```bash
# List files and directories
ls /arc/projects/[project]/

# Copy files
cp mydata.fits /arc/projects/[project]/data/

# Create directories
mkdir /arc/projects/[project]/survey_analysis/

# Move/rename files
mv /arc/projects/[project]/old.fits /arc/projects/[project]/new.fits

# Remove files
rm /arc/projects/[project]/temp/old_data.fits
```



### Bulk Operations

> Note: `vsync` and `vcp` are always recursive; no `--recursive` flag is needed.


#### Vault (VOSpace API)

```bash
# Sync entire directories to Vault
vsync ./local_data/ vos:[user]/backup/

# Download project data from Vault
vsync vos:[project]/survey_data/ ./project_data/

# Upload analysis results to Vault
vsync ./results/ vos:[user]/analysis_outputs/
```


#### ARC (VOSpace API, outside CANFAR)

```bash
# Sync entire directories to ARC
vsync ./local_data/ arc:projects/[project]/backup/

# Download project data from ARC
vsync arc:projects/[project]/survey_data/ ./project_data/

# Upload analysis results to ARC
vsync ./results/ arc:projects/[project]/analysis_outputs/
```



## Python API


### Basic Usage

```python
import vos

# Initialize client
client = vos.Client()


# List directory contents in Vault
files_vault = client.listdir("vos:[user]/")
print(files_vault)

# List directory contents in ARC
files_arc = client.listdir("arc:projects/[project]/")
print(files_arc)

# Check if file exists in Vault
exists_vault = client.isfile("vos:[user]/data.fits")

# Check if file exists in ARC
exists_arc = client.isfile("arc:projects/[project]/data.fits")

# Get file info from Vault
info_vault = client.get_info("vos:[user]/data.fits")
print(f"Size: {info_vault['size']} bytes")
print(f"Modified: {info_vault['date']}")

# Get file info from ARC
info_arc = client.get_info("arc:projects/[project]/data.fits")
print(f"Size: {info_arc['size']} bytes")
print(f"Modified: {info_arc['date']}")
```


### File Operations

```python

# Copy file to Vault
client.copy("mydata.fits", "vos:[user]/data/mydata.fits")

# Copy file to ARC
client.copy("mydata.fits", "arc:projects/[project]/data/mydata.fits")

# Copy file from Vault
client.copy("vos:[user]/data/results.txt", "./results.txt")

# Copy file from ARC
client.copy("arc:projects/[project]/data/results.txt", "./results.txt")

# Create directory in Vault
client.mkdir("vos:[user]/new_project/")

# Create directory in ARC
client.mkdir("arc:projects/[project]/new_project/")

# Delete file in Vault
client.delete("vos:[user]/temp/old_file.txt")

# Delete file in ARC
client.delete("arc:projects/[project]/temp/old_file.txt")
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
                client.copy(output_path, f"vos:[user]/processed/{fits_file}")
            else:
                client.copy(output_path, f"arc:projects/[project]/processed/{fits_file}")

        # Clean up temporary file
        os.remove(local_path)

# Usage

process_fits_files("vos:[user]/raw_data", "./processed/")
process_fits_files("arc:projects/[project]/raw_data", "./processed/")
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
        client.listdir("vos:[project]/")
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
    input_remote_vault = "vos:[project]/raw_data"
    input_remote_arc = "arc:projects/[project]/raw_data"
    output_remote_vault = "vos:[user]/processed_results"
    output_remote_arc = "arc:projects/[project]/processed_results"
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
vcp vos:[project]/input/data.fits ./input.fits
# Download input data from ARC
vcp arc:projects/[project]/input/data.fits ./input_arc.fits

# Process data
python analysis_script.py input.fits output.fits

# Upload results to Vault
vcp output.fits vos:[project]/results/processed_$(date +%Y%m%d).fits
# Upload results to ARC
vcp output.fits arc:projects/[project]/results/processed_$(date +%Y%m%d).fits

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
vls -l vos:[user]/file.fits
# Check file permissions in ARC
vls -l arc:home/[user]/script.py

# Check directory access in Vault
vls vos:[project]/
# Check directory access in ARC
vls arc:projects/[project]/
```
