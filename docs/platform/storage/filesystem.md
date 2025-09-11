# Filesystem Access

**CANFAR's ARC storage systems as filesystems, SSHFS mounting from external computers, and permission management.**

!!! abstract "🎯 Filesystem Guide Overview"
    **Master direct storage access:**
    
    - **Session Access**: How ARC storage appears within CANFAR computing sessions
    - **SSHFS Mounting**: Accessing CANFAR storage from your local computer
    - **Access Control Lists**: Fine-grained permissions for collaborative research  
    - **Performance Tips**: Optimising filesystem operations and troubleshooting

ARC storage (Home and Projects) can be accessed as standard Unix filesystems both within CANFAR sessions and from external computers via SSHFS. This provides familiar file operations and integrates seamlessly with existing tools and workflows.

## 🗂️ ARC Storage as Filesystems

### Within CANFAR Sessions

When you start any CANFAR session (Notebook, Desktop, or batch job), ARC storage is automatically mounted as standard directories:

```bash
# Automatic mounts in every session
/arc/home/[user]/          # Your personal 10GB space
/arc/projects/[project]/   # Shared project spaces (if member)
/scratch/                  # Temporary session storage
```

### Directory Structure and Conventions

#### ARC Home Directory (`/arc/home/[user]/`)

Typically the home directory tree structure will be as follows:

```text
/arc/home/[user]/
├── .ssh/                   # SSH keys and config
│   ├── authorized_keys     # Public keys for SSHFS access
│   └── config              # SSH client configuration
├── .jupyter/               # Jupyter configuration
├── .bashrc                 # Shell configuration
├── .profile                # Environment setup
├── bin/                    # Personal scripts and tools
├── config/                 # Application configurations
└── work/                   # Personal analysis work
```

**Recommended Use:**
- Configuration files and dotfiles
- Personal code, scripts and utilities
- SSH keys for external access
- Small reference files and notes

#### ARC Projects Directory (`/arc/projects/[project]/`)

Used for team project use. For example, for a propcessing pipeline analysis:
```text
/arc/projects/[project]/
├── data/
│   ├── raw/                # Original datasets
│   ├── processed/          # Reduced/calibrated data
│   ├── catalogs/           # Reference catalogs
│   └── archives/           # Archived datasets
├── code/
│   ├── pipelines/          # Data processing workflows  
│   ├── analysis/           # Analysis scripts
│   ├── notebooks/          # Jupyter notebooks
│   └── tools/              # Project-specific utilities
├── results/
│   ├── plots/              # Figures and visualisations
│   ├── tables/             # Output catalogues and measurements
│   ├── papers/             # Manuscripts and drafts
│   └── presentations/      # Conference materials
├── docs/
│   ├── README.md           # Project documentation
│   ├── data_notes.md       # Dataset descriptions
│   └── procedures.md       # Analysis procedures
└── scratch_archive/        # Backed up scratch work
```

## 🏠 Direct Filesystem Access (Within Sessions)

### Basic Operations

All standard Unix filesystem commands work directly:

```bash
# Navigation
cd /arc/projects/[project]/
pwd
ls -la

# File operations
cp source.fits destination.fits
mv old_name.fits new_name.fits
rm unwanted_file.fits

# Directory operations
mkdir -p data/2024/observations/
rmdir empty_directory/
find . -name "*.fits" -type f

# Permissions
chmod 644 data_file.fits          # Read/write owner, read others
chmod 755 analysis_script.py      # Executable script
chgrp projectgroup shared_data/   # Change group ownership
```

### Working with Large Datasets

```bash
# Check available space
df -h /arc/projects/[project]/
df -h /arc/home/[user]/

# Monitor space usage
du -sh /arc/projects/[project]/*
du -h --max-depth=2 /arc/projects/[project]/

# Efficient data movement
rsync -avP /scratch/processed_data/ /arc/projects/[project]/results/

# Archive old data
tar -czf old_observations_2023.tar.gz data/2023/
mv old_observations_2023.tar.gz archives/
```

### Linking and Shortcuts

```bash
# Create symbolic links for easy access
ln -s /arc/projects/survey/data/master_catalogue.fits ~/current_catalogue.fits
ln -s /arc/projects/[project]/ ~/project

# Hard links (same filesystem only)
ln /arc/projects/shared/reference.fits /arc/home/[user]/my_reference.fits

# Quick navigation with variables
export PROJECT_DIR="/arc/projects/[project]"
cd $PROJECT_DIR/data
```

## 🌐 SSHFS: Remote Filesystem Access

SSHFS allows you to mount CANFAR's ARC storage on your local computer as if it were a local directory, enabling seamless integration with local tools and workflows.

### Prerequisites

#### Local Computer Setup

=== "macOS"
    ```bash
    # Install macFUSE and SSHFS
    brew install --cask macfuse
    brew install sshfs
    
    # Restart or logout/login after installation
    ```

=== "Linux (Ubuntu/Debian)"
    ```bash
    # Install SSHFS
    sudo apt update
    sudo apt install sshfs
    
    # Add user to fuse group
    sudo usermod -a -G fuse $USER
    # Logout and login again
    ```

=== "Linux (Fedora/RedHat)"
    ```bash
    # Install SSHFS
    sudo dnf install sshfs
    
    # Add user to fuse group
    sudo usermod -a -G fuse $USER
    ```

#### CANFAR Side Setup

You need to set up SSH key authentication on your CANFAR account:

1. **Create SSH key pair** (on your local computer):
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/canfar_key
   # Enter passphrase when prompted (recommended)
   ```

2. **Upload public key to CANFAR**:
   
   **Method 1: Via Web Interface**
   - Navigate to [ARC File Manager](https://www.canfar.net/storage/arc/list/home)
   - Go to your home directory
   - Create `.ssh` folder if it doesn't exist
   - Upload your `~/.ssh/canfar_key.pub` as `authorized_keys` (if it already exists, you will have to append to the end of the file)
   
   **Method 2: Via existing session**
   ```bash
   # In a CANFAR session, copy your public key content to:
   mkdir -p /arc/home/[user]/.ssh
   # Paste your public key content into authorized_keys file
   nano /arc/home/[user]/.ssh/authorized_keys
   chmod 700 /arc/home/[user]/.ssh
   chmod 600 /arc/home/[user]/.ssh/authorized_keys
   ```

### Mounting ARC Storage

#### Basic Mount

```bash
# Create local mount point
mkdir ~/canfar_arc

# Mount ARC storage
sshfs -p 64022 -i ~/.ssh/canfar_key \
      -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=10 \
      [user]@ws-uv.canfar.net:/ ~/canfar_arc/

# On macOS, you may have to add defer_permissions option:
sshfs -p 64022 -i ~/.ssh/canfar_key \
      -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=10,defer_permissions \
      [user]@ws-uv.canfar.net:/ ~/canfar_arc/
```

#### Advanced Mount Options

```bash
# Mount with optimizations for large files
sshfs -p 64022 -i ~/.ssh/canfar_key \
      -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=10 \
      -o cache=yes,kernel_cache,compression=yes \
      -o Ciphers=aes128-ctr \
      [user]@ws-uv.canfar.net:/ ~/canfar_arc/

# Mount specific project only
sshfs -p 64022 -i ~/.ssh/canfar_key \
      -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=10 \
      [user]@ws-uv.canfar.net:/arc/projects/[project] ~/project_mount/
```

#### Connection Configuration

Create `~/.ssh/config` for easier connections:

```text
Host canfar
    HostName ws-uv.canfar.net
    Port 64022
    User [user]
    IdentityFile ~/.ssh/canfar_key
    ServerAliveInterval 15
    ServerAliveCountMax 10
    Compression yes
```

Then mount with simpler command:
```bash
sshfs canfar:/ ~/canfar_arc/
```

### Using Mounted Storage

Once mounted, use CANFAR storage like any local directory:

```bash
# Navigate to your project
cd ~/canfar_arc/arc/projects/[project]/

# Copy files from local to CANFAR
cp ~/local_analysis.py ~/canfar_arc/arc/projects/[project]/code/

# Edit files with local editor
code ~/canfar_arc/arc/home/[user]/.bashrc

# Run local tools on CANFAR data
python analyze_data.py ~/canfar_arc/arc/projects/[project]/data/observations.fits

# Sync directories
rsync -avz ~/local_scripts/ ~/canfar_arc/arc/projects/[project]/code/
```

### Unmounting

```bash
# Unmount when finished
umount ~/canfar_arc
# or on macOS:
diskutil unmount ~/canfar_arc

# Force unmount if needed
umount -f ~/canfar_arc
# or
fusermount -u ~/canfar_arc
```

## 🔐 Access Control and Permissions

### Understanding ARC Permissions

ARC storage uses traditional Unix permissions combined with group-based access control:

#### Permission Types

```bash
# View detailed permissions
ls -l /arc/projects/[project]/

# Example output:
# drwxrwxr--  projectgroup  data/
# -rw-rw-r--  projectgroup  analysis.py
# -rwx------  username      private_script.py

# Permission breakdown:
# d = directory, - = file
# rwx = owner permissions (read/write/execute)
# rwx = group permissions  
# r-- = other permissions
```

#### User and Group Information

```bash
# Check your user ID and groups
id
whoami
groups

# Check file ownership
stat /arc/projects/[project]/somefile.fits

# View group membership
getent group [project]
```

### Managing Permissions

#### Setting File Permissions

```bash
# Make file readable by group
chmod g+r data_file.fits

# Make script executable
chmod +x analysis_script.py

# Set specific permission modes
chmod 664 shared_data.fits     # rw-rw-r--
chmod 755 public_script.py     # rwxr-xr-x
chmod 600 private_config.txt   # rw-------

# Recursive permission changes
chmod -R g+rw shared_directory/
```

#### Group Management

Group membership is managed through CANFAR's Group Management system:

1. **Navigate to**: [Group Management](https://www.canfar.net/groups/)
2. **Create or modify groups**: Add/remove users from project groups
3. **Apply permissions**: Use `chgrp` to assign files to groups

```bash
# Change group ownership
chgrp projectgroup /arc/projects/[project]/shared_data.fits

# Change recursively
chgrp -R projectgroup /arc/projects/[project]/shared_results/

# Set default group for new files in directory
chmod g+s /arc/projects/[project]/shared_directory/
```

### Access Control Lists (ACLs)

For fine-grained permissions beyond standard Unix permissions:

```bash
# View current ACLs
getfacl /arc/projects/[project]/sensitive_data.fits

# Set ACL for specific user
setfacl -m u:collaborator:r /arc/projects/[project]/data.fits

# Set ACL for group
setfacl -m g:external_collaborators:r /arc/projects/[project]/

# Remove ACL
setfacl -x u:former_collaborator /arc/projects/[project]/data.fits

# Set default ACLs for directory
setfacl -d -m g:projectgroup:rw /arc/projects/[project]/shared/
```

## 🔧 Optimization and Best Practices

### Performance Optimization

#### Local Filesystem Operations

```bash
# Use rsync for efficient synchronization
rsync -avz --progress ~/local_data/ /arc/projects/[project]/backup/

# Monitor I/O performance
iostat -x 1    # Live I/O statistics
iotop          # Process I/O usage

# Optimize for large files
# Use /scratch/ for intensive processing
cp /arc/projects/[project]/large_dataset.fits /scratch/
process_data /scratch/large_dataset.fits
cp /scratch/results.fits /arc/projects/[project]/outputs/
```

#### SSHFS Performance Tips

```bash
# Optimize SSHFS for different use cases

# For frequent small file access:
sshfs -o cache=yes,kernel_cache,attr_timeout=3600,entry_timeout=3600 \
      canfar:/ ~/canfar_arc/

# For large file transfers:
sshfs -o cache=no,compression=yes,Ciphers=aes128-ctr \
      canfar:/ ~/canfar_arc/

# For read-only access (faster):
sshfs -o ro,cache=yes,kernel_cache \
      canfar:/ ~/canfar_arc/
```

### Workflow Integration

#### Local Development with CANFAR Data

```bash
# Create development environment
mkdir ~/canfar_project/
cd ~/canfar_project/

# Mount CANFAR storage as subdirectory
mkdir canfar_data
sshfs canfar:/arc/projects/[project] canfar_data/

# Create local working directory
mkdir local_work
cd local_work

# Symlink to CANFAR data for easy access
ln -s ../canfar_data/data ./data
ln -s ../canfar_data/code ./shared_code

# Work locally with CANFAR data
python shared_code/analysis.py data/observations.fits
```

#### Automated Backup Scripts

```bash
#!/bin/bash
# backup_to_canfar.sh - Automated backup script

LOCAL_DIR="$HOME/important_work"
CANFAR_MOUNT="$HOME/canfar_arc"
BACKUP_DIR="$CANFAR_MOUNT/arc/home/[user]/backups"

# Check if CANFAR is mounted
if ! mountpoint -q "$CANFAR_MOUNT"; then
    echo "Mounting CANFAR storage..."
    sshfs canfar:/ "$CANFAR_MOUNT"
fi

# Create backup with timestamp
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$DATE"

echo "Creating backup: $BACKUP_PATH"
rsync -avz --progress "$LOCAL_DIR/" "$BACKUP_PATH/"

# Keep only last 5 backups
cd "$BACKUP_DIR"
ls -t | tail -n +6 | xargs rm -rf

echo "Backup completed successfully"
```



## 🛠️ Troubleshooting

### Common Issues and Solutions

#### SSHFS Connection Problems

```bash
# Debug SSHFS connection
sshfs -d -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=10,defer_permissions -p 64022 [user]@ws-uv.canfar.net:/ $HOME/canfar_arc
# Check mount status
mount | grep sshfs
df -h | grep sshfs
```

#### Permission Denied Errors

```bash
# Check your group membership
groups
id

# Verify file permissions
ls -la /arc/projects/[project]/problematic_file

# Check directory execute permissions
ls -ld /arc/projects/[project]/

```

#### Performance Issues

```bash
# Check filesystem I/O
iostat -x 1

# Monitor network usage (for SSHFS)
netstat -i
iftop

# Test SSHFS performance
time ls -la ~/canfar_arc/projects/[project]/

# Remount with performance options
umount ~/canfar_arc
sshfs -o cache=yes,compression=yes canfar:/ ~/canfar_arc/
```

#### Storage Space Issues

```bash
# Check quota usage
df -h /arc/home/[user]/
df -h /arc/projects/[project]/

# Find large files
find /arc/projects/[project]]/ -type f -size +100M -exec ls -lh {} \;

# Clean up space
du -sh /arc/projects/[project]/* | sort -hr
# Remove or archive large unnecessary files
```

### Diagnostic Commands

```bash
# System information
uname -a
mount | grep arc
df -h

# Network connectivity
ping ws-uv.canfar.net
telnet ws-uv.canfar.net 64022

# SSH key verification
ssh-keygen -lf ~/.ssh/canfar_key.pub
ssh-add -l

# SSHFS troubleshooting
fusermount -V
sshfs --version

# Permission debugging
getfacl /arc/projects/[project]/
namei -l /arc/projects/[project]/path/to/file
```

## 🔗 Integration Examples

### IDE and Editor Integration

#### VS Code with Remote Filesystem

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "/usr/bin/python",
    "files.watcherExclude": {
        "**/canfar_arc/**": true
    },
    "search.exclude": {
        "**/canfar_arc/**": true
    }
}
```

#### Jupyter Lab with SSHFS

```python
# In Jupyter Lab, access CANFAR data via mounted filesystem on your laptop
import pandas as pd
from astropy.io import fits

# Read data from mounted CANFAR storage
data_path = "$HOME/canfar_arc/arc/projects/[project]/data/"
catalog = pd.read_csv(f"{data_path}/catalog.csv")

# Process and save results back to CANFAR
results = process_data(catalog)
results.to_csv(f"{data_path}/processed_catalog.csv")
```

### Automated Workflows

#### Git Repository Sync

```bash
#!/bin/bash
# sync_code_to_canfar.sh

LOCAL_REPO="$HOME/my_analysis_code"
CANFAR_CODE="$HOME/canfar_arc/arc/projects/[project]/code"

cd "$LOCAL_REPO"

# Push local changes to git
git add .
git commit -m "Update analysis code"
git push origin main

# Sync to CANFAR
rsync -avz --exclude='.git' . "$CANFAR_CODE/"

echo "Code synchronized to CANFAR"
```
