# Data Transfers

**Moving data between CANFAR storage systems, external sources, and your local computer.**

!!! abstract "🎯 Transfer Methods Overview"
    **Efficient data movement strategies:**
    
    - **Web Interfaces**: Simple uploads and downloads for small files
    - **Command-Line Tools**: Efficient transfers for large datasets
    - **Automated Workflows**: Scripted transfers and synchronisation
    - **Performance Optimisation**: Choosing the right method for your data size

Efficient data transfer is essential for astronomy workflows. CANFAR provides multiple transfer methods optimised for different scenarios, from small file uploads to large dataset synchronisation.

## 🔄 Transfer Overview

### Transfer Types by Method

| Method | Best For | Speed | Complexity | Interactive | Automated |
|--------|----------|-------|------------|-------------|-----------|
| **Web Upload/Download** | Small files (<1GB) | Slow | Simple | ✅ | ❌ |
| **Direct URLs** | Medium files, scripting | Medium | Simple | ⚠️ | ✅ |
| **VOSpace CLI** | All sizes, Vault access | Medium | Medium | ✅ | ✅ |
| **SSHFS Mount** | Local file operations | Medium | Medium | ✅ | ⚠️ |
| **rsync via SSHFS** | Large datasets, sync | Fast | Advanced | ⚠️ | ✅ |

### Storage System Access

| Source → Destination | Method | Command Example |
|---------------------|--------|-----------------|
| **Local → ARC Projects** | SSHFS, Direct URL, VOSpace | `vcp file.fits vos:/arc:projects/[project]/` |
| **Local → Vault** | VOSpace CLI, Web | `vcp file.fits vos:[user]/` |
| **Local → Scratch** | Only during sessions | `cp file.fits /scratch/` (within session) |
| **ARC → Vault** | VOSpace CLI | `vcp /arc/projects/[project]/file.fits vos:[user]/` |
| **Vault → ARC** | VOSpace CLI | `vcp vos:[user]/file.fits /arc/projects/[project]/` |
| **Scratch ↔ ARC** | Direct copy | `cp /scratch/file.fits /arc/projects/[project]/` |

## 📤 Upload Methods

### Small Files (<1GB): Web Interface

#### ARC Projects and Home

1. **Navigate to storage**: [ARC File Manager](https://www.canfar.net/storage/arc/list/)
2. **Select destination**: Choose your home or project directory
3. **Upload files**: Click "Add" → "Upload Files" 
4. **Select files**: Choose files from your computer
5. **Confirm upload**: Click "Upload" then "OK"

Note on a notebook session you can also use the JupyterLab **Upload** button.

#### Vault (VOSpace)

1. **Navigate to Vault**: [VOSpace File Manager](https://www.canfar.net/storage/vault/list/)
2. **Select destination**: Browse to your space
3. **Upload files**: Same process as ARC storage
4. **Set permissions**: Right-click → Properties to set sharing permissions

### Medium Files (1-100GB): Command Line

#### Using Direct URLs (ARC only)

```bash
# Authenticate first
cadc-get-cert -u [user]

# Upload to ARC Home
curl -E ~/.ssl/cadcproxy.pem \
     -T myfile.fits \
     https://ws-uv.canfar.net/arc/files/home/[user]/myfile.fits

# Upload to ARC Projects  
curl -E ~/.ssl/cadcproxy.pem \
     -T myfile.fits \
     https://ws-uv.canfar.net/arc/files/projects/[project]/myfile.fits
```

#### Using VOSpace CLI

```bash
# Install VOS tools (if not already available)
pip install vos

# Authenticate
cadc-get-cert -u [user]

# Upload to Vault
vcp myfile.fits vos:[user]/data/

# Upload to ARC via VOSpace API
vcp myfile.fits arc:projects/[project]/data/

# Upload with progress monitoring
vcp --verbose myfile.fits vos:[user]/large_files/
```

### Large Files (>100GB): Advanced Methods

#### SSHFS Mount + rsync

```bash
# 1. Mount CANFAR storage locally
mkdir ~/canfar_mount
sshfs -p 64022 [user]@ws-uv.canfar.net:/ ~/canfar_mount

# 2. Sync large datasets with rsync
rsync -avzP --partial \
      ./large_dataset/ \
      ~/canfar_mount/arc/projects/[project]/data/

# 3. Unmount when complete
umount ~/canfar_mount
```

#### VOSpace Bulk Transfer

```bash
# Sync entire directories
vsync ./local_data/ vos:[user]/backup/

# Parallel transfers (faster for many files)
vcp --nstreams=4 large_file.tar vos:[user]/archives/
```

## 📥 Download Methods

### From ARC Storage

#### Web Interface

1. **Navigate**: [ARC File Manager](https://www.canfar.net/storage/arc/list/)
2. **Select files**: Check boxes next to desired files
3. **Download options**:
   - **ZIP**: Single archive (recommended for multiple files)
   - **URL List**: Generate download links for scripting
   - **HTML List**: Individual download links

#### Command Line

```bash
# Direct URL download
curl -E ~/.ssl/cadcproxy.pem \
     https://ws-uv.canfar.net/arc/files/home/[user]/myfile.fits \
     -o myfile.fits

# Via VOSpace API
vcp arc:home/[user]/myfile.fits ./

# Multiple files with wildcards
vcp "arc:projects/[project]/data/*.fits" ./local_data/
```

### From Vault (VOSpace)

#### Command Line

```bash
# Single file
vcp vos:[user]/data.fits ./

# Directory with all contents
vcp vos:[user]/survey_data/ ./local_survey/
```

#### Python API

```python
import vos

client = vos.Client()

# Download single file
client.copy("vos:[user]/data.fits", "./local_data.fits")

# Download with progress callback
def progress_callback(bytes_transferred, total_bytes):
    percent = (bytes_transferred / total_bytes) * 100
    print(f"Progress: {percent:.1f}%")

client.copy("vos:[user]/large_file.fits", 
           "./large_file.fits", 
           callback=progress_callback)
```

## 🔄 Inter-Storage Transfers

### Moving Data Between Storage Systems

#### Scratch to ARC (Within Sessions)

```bash
# Process data in scratch for speed
cp /arc/projects/[project]/raw_data.fits /scratch/
python reduce_data.py /scratch/raw_data.fits

# Save results to permanent storage
cp /scratch/processed_data.fits /arc/projects/[project]/results/
cp /scratch/analysis_plots/ /arc/projects/[project]/figures/
```

#### ARC to Vault (Archival)

```bash
# Archive completed project results
vcp /arc/projects/[project]/final_results/ vos:[user]/archives/project2024/
```

#### Vault to ARC (Project Setup)

```bash
# Import archived data for new analysis
vcp vos:shared_project/calibrated_data/ /arc/projects/[project]/data/

# Import specific datasets
vcp "vos:public_surveys/gaia_dr3/*.fits" /arc/projects/[project]/catalogues/
```

### Automated Workflow Example

```bash
#!/bin/bash
# Complete data processing workflow

set -e  # Exit on error

PROJECT_DIR="/arc/projects/[project]"
SCRATCH_DIR="/scratch"

echo "Starting data processing pipeline..."

# 1. Download raw data from Vault to scratch
echo "Downloading raw data..."
vcp vos:[user]/raw_observations/obs_*.fits ${SCRATCH_DIR}/

# 2. Process data in scratch (fastest storage)
echo "Processing data..."
cd ${SCRATCH_DIR}
for file in obs_*.fits; do
    python calibrate.py "$file" "cal_${file}"
done

# 3. Save intermediate results to ARC
echo "Saving calibrated data..."
mkdir -p ${PROJECT_DIR}/calibrated/
cp cal_*.fits ${PROJECT_DIR}/calibrated/

# 4. Further analysis
echo "Running analysis..."
python analyze_all.py ${PROJECT_DIR}/calibrated/ > analysis_results.txt

# 5. Save final results to ARC and archive to Vault
echo "Saving final results..."
cp analysis_results.txt ${PROJECT_DIR}/results/
cp final_plots/*.png ${PROJECT_DIR}/figures/

# Archive to Vault
vcp ${PROJECT_DIR}/results/ vos:[user]/completed_projects/$(date +%Y%m%d)/

echo "Pipeline completed successfully!"
```

## 📊 Performance Optimization

### Transfer Speed Optimization

#### For Many Small Files

```bash
# Bundle small files into archives
tar -czf analysis_scripts.tar.gz scripts/
vcp analysis_scripts.tar.gz vos:[user]/code/

# Use directory sync instead of individual copies
vsync --nstreams=4 ./many_small_files/ vos:[user]/collection/
```

### Network Performance Tips

#### Optimal Transfer Times

- **Best performance**: Off-peak hours (evenings, weekends)
- **Avoid**: Peak research hours (9 AM - 5 PM Pacific)

#### Connection Optimization

```bash
# Check network speed to CANFAR
ping ws-uv.canfar.net

# Test transfer speed with small file
time vcp test_file.fits vos:[user]/speed_test/
```

## 🚨 Error Handling and Recovery

### Common Transfer Issues

#### Authentication Errors

```bash
# Certificate expired
ERROR:: Expired cert. Update by running cadc-get-cert

# Solution: Refresh certificate
cadc-get-cert -u [user]

# Check certificate validity
cadc-get-cert --days-valid
```

#### Network Timeouts

```bash
# Retry with exponential backoff
for i in {1..3}; do
    vcp file.fits vos:[user]/ && break
    sleep $((2**i))
done
```

### Robust Transfer Script

```python
#!/usr/bin/env python
"""
Robust file transfer with retry logic
"""
import vos
import time
import sys
from pathlib import Path

def robust_transfer(source, destination, max_retries=3):
    """Transfer file with retry logic"""
    client = vos.Client()
    
    for attempt in range(max_retries):
        try:
            print(f"Transfer attempt {attempt + 1}: {source} → {destination}")
            client.copy(source, destination)
            print(f"✓ Transfer successful")
            return True
            
        except Exception as e:
            print(f"✗ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"Transfer failed after {max_retries} attempts")
                return False

# Usage
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python robust_transfer.py <source> <destination>")
        sys.exit(1)
    
    source, destination = sys.argv[1], sys.argv[2]
    success = robust_transfer(source, destination)
    sys.exit(0 if success else 1)
```

## 📋 Transfer Checklists

### Pre-Transfer Checklist

- [ ] **Authentication**: Valid CADC certificate (`cadc-get-cert`)
- [ ] **Permissions**: Write access to destination directory
- [ ] **Space**: Sufficient quota in destination storage
- [ ] **Network**: Stable connection for large transfers
- [ ] **Backup**: Important data backed up before moving

### Post-Transfer Verification

```bash
# Verify file integrity
vls -l vos:[user]/transferred_file.fits  # Check size and timestamp

# Compare checksums (if available)
vcp --head vos:[user]/data.fits | grep MD5

# Test file readability
python -c "from astropy.io import fits; fits.open('test_file.fits')"
```

### Transfer Planning Template

```markdown
## Transfer Plan: [Project Name]

**Data Description**: 
- Size: ___GB
- File count: ___
- Type: Raw/Processed/Results

**Source**: _______________
**Destination**: ___________
**Method**: _______________

**Timeline**:
- Start: ____________
- Estimated completion: ___________

**Verification**:
- [ ] File count matches
- [ ] Total size matches  
- [ ] Sample files readable
- [ ] Permissions set correctly

**Backup**: _______________
```

## 🔗 Integration Examples

### Jupyter Notebook Upload

Within a CANFAR Jupyter session:

```python
# Upload files using the Jupyter interface
# 1. Click the "Upload" button in file browser
# 2. Select files from your computer
# 3. Files appear in current directory

# Move uploaded files to appropriate storage
import shutil
shutil.move('uploaded_data.fits', '/arc/projects/[project]/data/')

# Or copy to scratch for processing
shutil.copy('/arc/projects/[project]/data.fits', '/scratch/')
```

### Batch Job Data Staging

```bash
#!/bin/bash
# Batch job with data staging

# Download input data
vcp vos:project/input_data.tar.gz /scratch/
cd /scratch
tar -xzf input_data.tar.gz

# Process data
python analysis.py input_data/

# Upload results
tar -czf results_$(date +%Y%m%d).tar.gz results/
vcp results_*.tar.gz vos:[user]/job_outputs/

# Cleanup
rm -rf /scratch/*
```

### External Data Import

```bash
# Download from astronomical archives
wget -O survey_data.fits "https://archive.eso.org/..."

# Upload to CANFAR
vcp survey_data.fits vos:[user]/external_data/

# Or direct to project space
curl -E ~/.ssl/cadcproxy.pem \
     -T survey_data.fits \
     https://ws-uv.canfar.net/arc/files/projects/[project]/survey_data.fits
```
