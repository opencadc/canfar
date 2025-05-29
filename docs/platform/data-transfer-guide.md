<!-- filepath: /Users/fabbros/src/science-containers/docs/data-transfer-guide.md -->

# Complete Data Transfer Guide

> **📚 Related Guides:**
>
> - [Storage Systems Overview →](storage-systems-guide.md) - Understand ARC, Scratch, and VOSpace differences
> - [Container Building Guide →](container-building-guide.md) - Data access in custom containers
> - [Headless Execution Guide →](headless-execution-guide.md) - Automated data processing workflows
> - [SSH File System Guide →](user-guide/sshfs-setup.md) - Detailed sshfs setup

## 🎯 Choose Your Method

Different transfer methods work best for different scenarios:

| Method            | Best For                    | File Size | Setup Required   | Speed  | Reliability |
|-------------------|-----------------------------|-----------|------------------|--------|-------------|
| **Web Interface** | Small files, occasional use | <1GB      | None             | Medium | High        |
| **Notebook Upload** | Quick file upload to sessions | <100MB    | None             | Fast   | High        |
| **sshfs**         | Interactive file access     | Any       | One-time setup   | Fast   | Medium      |
| **VOSpace Tools** | Reliable bulk transfers     | >1GB      | Install tools    | Medium | Very High   |
| **Direct URLs**   | Automated/scripted transfers| Any       | Certificate setup| Fast   | High        |

## 🌐 Web Interface (Easiest)

### CANFAR File Manager

Access at: <https://www.canfar.net/storage/arc/list>

**Upload Files:**

1. Navigate to your target directory
2. Click "Add" → "Upload File(s)"
3. Select files or drag-and-drop
4. Click "Upload"

**Download Files:**

1. Browse to the file location
2. Right-click file → "Download"
3. Or select multiple files → "Actions" → "Download"

**Best for:** Occasional file transfers, small datasets, web-based workflow

## 💻 sshfs - Mount Storage as Local Drive

=== "Ubuntu/Debian"

    **1. Install sshfs**

        sudo apt-get install sshfs

    **2. Set up SSH keys**

        # Generate key pair if you don't have one
        ssh-keygen -t rsa -b 4096

        # Copy public key to CANFAR
        # Upload ~/.ssh/id_rsa.pub to /arc/home/username/.ssh/authorized_keys
        # via web interface

    **3. Mount the filesystem**

        # Create local mount point
        mkdir ~/canfar

        # Mount
        sshfs -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=10 \\
          -p 64022 username@ws-uv.canfar.net:/ ~/canfar

=== "macOS"

    **1. Install sshfs**

        brew install macfuse sshfs
        # or download from https://osxfuse.github.io/

    **2. Set up SSH keys**

        # Generate key pair if you don't have one
        ssh-keygen -t rsa -b 4096

        # Copy public key to CANFAR
        # Upload ~/.ssh/id_rsa.pub to /arc/home/username/.ssh/authorized_keys
        # via web interface

    **3. Mount the filesystem**

        # Create local mount point
        mkdir ~/canfar

        # Mount
        sshfs -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=10,defer_permissions \\
          -p 64022 username@ws-uv.canfar.net:/ ~/canfar

### Daily Usage

Once mounted, access CANFAR storage like local directories:

    # Navigate to your project
    cd ~/canfar/arc/projects/yourproject

    # Copy files TO CANFAR
    cp /local/data/dataset.fits ~/canfar/arc/projects/yourproject/data/

    # Copy files FROM CANFAR
    cp ~/canfar/arc/projects/yourproject/results/analysis.txt ~/local/results/

    # Use rsync for large transfers
    rsync -avz --progress /local/bigdata/ ~/

    # Navigate to your project
    cd ~/canfar/arc/projects/yourproject

    # Copy files TO CANFAR
    cp /local/data/dataset.fits ~/canfar/arc/projects/yourproject/data/

    # Copy files FROM CANFAR
    cp ~/canfar/arc/projects/yourproject/results/analysis.txt ~/local/results/

    # Use rsync for large transfers
    rsync -avz --progress /local/bigdata/ ~/canfar/arc/projects/yourproject/bigdata/

### Unmounting

=== "Linux"

    # When finished
    umount ~/canfar

    # If stuck
    fusermount -u ~/canfar

=== "macOS"

    # When finished
    umount ~/canfar

    # If stuck
    umount -f ~/canfar

**Best for:** Interactive file access, regular file management, large directory trees

## 🛠️ VOSpace Tools - Reliable Command Line

### Installation

    # Install via pip
    pip install vostools

    # Or via conda
    conda install -c conda-forge vostools

### Authentication

    # Get CADC certificate
    cadc-get-cert -u yourusername
    # Enter your CADC password when prompted

### Basic Commands

**Copy files TO CANFAR:**

    # Single file to home directory
    vcp localfile.txt arc:home/username/

    # Single file to project space
    vcp dataset.fits arc:projects/yourproject/data/

    # Entire directory
    vcp -r /local/data/ arc:projects/yourproject/data/

**Copy files FROM CANFAR:**

    # Single file from CANFAR
    vcp arc:home/username/results.txt ./

    # Directory from CANFAR
    vcp -r arc:projects/yourproject/processed/ ./local_copy/

**List and manage files:**

    # List files
    vls arc:home/username/
    vls arc:projects/yourproject/

    # Create directory
    vmkdir arc:projects/yourproject/new_analysis/

    # Remove files
    vrm arc:projects/yourproject/temporary_file.txt

**Work with VOSpace:**

    # Copy to long-term archive
    vcp dataset.fits vos:username/published_data/

    # Copy from VOSpace to CANFAR
    vcp vos:username/archive/olddata.fits arc:projects/yourproject/reference/

### Advanced Usage

    # Resume interrupted transfers
    vcp --resume large_file.tar.gz arc:projects/yourproject/

    # Verify transfer integrity
    vcp --checksum file.fits arc:projects/yourproject/data/

    # Monitor progress
    vcp --progress /local/bigdata.tar.gz arc:projects/yourproject/

**Best for:** Large file transfers, batch operations, reliable transfers, automation

## 🔗 Direct URLs with curl

### Setup Authentication

    # Get CADC certificate
    cadc-get-cert -u yourusername
    # Certificate saved to ~/.ssl/cadcproxy.pem

### Upload Files

    # Upload to home directory
    curl -E ~/.ssl/cadcproxy.pem \\
      https://ws-uv.canfar.net/arc/files/home/username/filename.txt \\
      -T localfile.txt

    # Upload to project space
    curl -E ~/.ssl/cadcproxy.pem \\
      https://ws-uv.canfar.net/arc/files/projects/yourproject/data/dataset.fits \\
      -T dataset.fits

    # Upload with progress bar
    curl -E ~/.ssl/cadcproxy.pem \\
      --progress-bar \\
      https://ws-uv.canfar.net/arc/files/projects/yourproject/bigfile.tar.gz \\
      -T bigfile.tar.gz

### Download Files

    # Download from CANFAR
    curl -E ~/.ssl/cadcproxy.pem \\
      https://ws-uv.canfar.net/arc/files/projects/yourproject/results.txt \\
      -o results.txt

    # Download with resume capability
    curl -E ~/.ssl/cadcproxy.pem -C - \\
      https://ws-uv.canfar.net/arc/files/projects/yourproject/large_result.tar.gz \\
      -o large_result.tar.gz

### Scripting Examples

    #!/bin/bash
    # Upload multiple files
    for file in *.fits; do
      echo "Uploading $file..."
      curl -E ~/.ssl/cadcproxy.pem \\
        https://ws-uv.canfar.net/arc/files/projects/yourproject/raw_data/$file \\
        -T "$file"
    done

    # Download file list
    curl -E ~/.ssl/cadcproxy.pem \\
      https://ws-uv.canfar.net/arc/files/projects/yourproject/file_list.txt \\
      | while read filename; do
        curl -E ~/.ssl/cadcproxy.pem \\
          https://ws-uv.canfar.net/arc/files/projects/yourproject/data/$filename \\
          -o $filename
      done

**Best for:** Automation, scripts, CI/CD pipelines, programmatic access

## 📓 Notebook Upload (In-Session)

### From Jupyter Interface

1. **File Browser** (left sidebar) → navigate to target directory
2. **Upload button** (↑ arrow icon) → select files
3. Files appear in current directory

### Programmatic Upload

    # From within a notebook
    import os
    from IPython.display import HTML

    # Create upload widget
    HTML(\'\'\'
    <input type="file" id="fileUpload" multiple>
    <script>
    document.getElementById(\'fileUpload\').addEventListener(\'change\', function(e) {
        var files = e.target.files;
        for (var i = 0; i < files.length; i++) {
            var file = files[i];
            var reader = new FileReader();
            reader.onload = function(e) {
                // File content in e.target.result
                // Save using Python kernel
            };
            reader.readAsText(file);
        }
    });
    </script>
    \'\'\')

**Best for:** Small files, quick uploads during analysis, notebook-centric workflows

## 🚀 Transfer Strategies by Use Case

### New Project Setup

    # 1. Create project structure
    ssh -p 64022 username@ws-uv.canfar.net
    mkdir -p /arc/projects/yourproject/{data,code,results,docs}

    # 2. Upload initial data via sshfs
    # (mount as shown above)
    rsync -avz --progress /local/project_data/ ~/canfar/arc/projects/yourproject/data/

    # 3. Set up code repository
    cd ~/canfar/arc/projects/yourproject/code/
    git clone https://github.com/yourusername/analysis_code.git

### Large Dataset Analysis

    # 1. Download to scratch for processing (fast I/O)
    # In a CANFAR session:
    cd /scratch
    wget -c https://archive.example.com/large_dataset.tar.gz

    # 2. Process in scratch
    tar xzf large_dataset.tar.gz
    python /arc/projects/yourproject/code/process_data.py large_dataset/

    # 3. Move results to permanent storage
    cp -r processed_results/ /arc/projects/yourproject/results/

### Regular Data Synchronization

    # Sync local analysis with CANFAR using rsync over sshfs
    rsync -avz --delete \\
      /local/analysis/ \\
      ~/canfar/arc/projects/yourproject/analysis/

    # Only upload modified files
    rsync -avz --update \\
      /local/new_data/ \\
      ~/canfar/arc/projects/yourproject/data/

### Collaboration Workflow

    # Team member A uploads data
    vcp team_dataset.fits arc:projects/ourproject/shared_data/

    # Team member B downloads for analysis
    vcp arc:projects/ourproject/shared_data/team_dataset.fits ./local_analysis/

    # Team member B uploads results
    vcp analysis_results.pdf arc:projects/ourproject/results/

## ⚡ Performance Tips

### Optimize Transfer Speed

    # Use compression for text/code files
    tar czf code.tar.gz code_directory/
    vcp code.tar.gz arc:projects/yourproject/

    # Parallel transfers for multiple files
    ls *.fits | xargs -n 1 -P 4 -I {} vcp {} arc:projects/yourproject/data/

    # Rsync with optimal settings
    rsync -avz --progress --partial --inplace \\
      large_file.tar.gz ~/canfar/arc/projects/yourproject/

### Handle Large Files

    # Split very large files
    split -b 1G large_file.tar.gz large_file_part_
    # Upload parts separately
    for part in large_file_part_*; do
      vcp $part arc:projects/yourproject/parts/
    done

    # Reassemble on CANFAR
    # (in a session)
    cd /arc/projects/yourproject/parts/
    cat large_file_part_* > ../large_file.tar.gz

### Verify Transfers

    # Compare file sizes
    ls -la local_file.fits
    vls -l arc:projects/yourproject/data/local_file.fits

    # Use checksums for critical data
    md5sum important_file.fits > important_file.md5
    vcp important_file.fits arc:projects/yourproject/data/
    vcp important_file.md5 arc:projects/yourproject/data/

    # Verify on CANFAR (in session)
    cd /arc/projects/yourproject/data/
    md5sum -c important_file.md5

## 🚨 Troubleshooting

### Common Issues

**sshfs connection drops:**

    # Reconnect automatically with retries
    sshfs -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=10 \\
      -p 64022 username@ws-uv.canfar.net:/ ~/canfar

**VOSpace tools authentication fails:**

    # Refresh certificate
    cadc-get-cert -u yourusername
    # Check certificate expiry
    cadc-info -u yourusername

**Transfer interrupted:**

    # Resume with curl
    curl -C - -E ~/.ssl/cadcproxy.pem [URL] -T file.txt

    # Resume with rsync
    rsync -avz --partial --progress file.txt ~/canfar/destination/

**Permission denied:**

    # Check CANFAR file permissions
    # (in a session)
    ls -la /arc/projects/yourproject/
    # Contact support if group permissions are wrong

### Getting Help

- **Transfer issues**: [support@canfar.net](mailto:support@canfar.net)
- **Performance questions**: [Slack #canfar-support](https://cadc.slack.com/archives/C01K60U5Q87)
- **Authentication problems**: Check [CADC documentation](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/doc/)

## Related Documentation

- **[Storage Systems Guide →](storage-systems-guide.md)** - Understand ARC, Scratch, and VOSpace differences and choose the right storage strategy
- **[Container Building Guide →](container-building-guide.md)** - Create custom containers with optimized data access patterns
- **[Headless Execution Guide →](headless-execution-guide.md)** - Automate data processing with batch jobs and API calls
- **[SSH Access Guide →](user-guide/access.md)** - Set up secure shell connections for command-line transfers
- **[Getting Started →](user-guide/first-login.md)** - Basic CANFAR account setup and interface introduction
