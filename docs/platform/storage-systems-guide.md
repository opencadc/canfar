# CANFAR Storage Systems Guide

> **📚 Related Guides:**
>
> - [Complete Data Transfer Methods →](data-transfer-guide.md) - How to move files to/from each storage system
> - [Container Building Guide →](container-building-guide.md) - Storage access in custom containers
> - [Headless Execution Guide →](headless-execution-guide.md) - Storage usage in batch processing
> - [Getting Started: Choose Interface →](user-guide/choose-interface.md) - Interface overview

## 📊 Storage Types Comparison

CANFAR provides different storage systems optimized for different use cases:

| Storage Type | Mount Path | Purpose | Speed | Persistence | Backup | Quota | Best For |
|--------------|------------|---------|-------|-------------|--------|-------|----------|
| **ARC Projects** | `/arc/projects/` | Active research data | Fast SSD | ✅ Permanent | ✅ Daily snapshots | Project-based (100GB-10TB) | Shared datasets, results |
| **ARC Home** | `/arc/home/` | Personal configs | Fast SSD | ✅ Permanent | ✅ Daily snapshots | 10GB default | Personal settings, keys |
| **Scratch** | `/scratch/` | Temporary processing | Fastest NVMe | ❌ Cleared nightly | ❌ No backup | Unlimited | Large intermediate files |
| **VOSpace** | `vos:` (external) | Long-term archive | Medium | ✅ Permanent | ✅ Geo-redundant | User/project based | Published data, final results |

## 🎯 When to Use Each Storage

### `/arc/projects/groupname/` - Main Research Storage

**✅ Use for:**

- Raw observational datasets
- Analysis scripts and code
- Results and publications
- Shared team resources
- Anything you want to keep

**Key Features:**

- Shared with all group members
- Backed up with 30-day retention
- Fast SSD storage for analysis
- Accessible from all sessions

**Example structure:**

```text
/arc/projects/myproject/
├── data/
│   ├── raw/           # Original datasets
│   ├── processed/     # Cleaned/calibrated data
│   └── catalogs/      # Reference catalogs
├── code/
│   ├── analysis/      # Analysis scripts
│   ├── pipelines/     # Data processing workflows
│   └── notebooks/     # Jupyter notebooks
├── results/
│   ├── plots/         # Figures and visualizations
│   ├── tables/        # Output catalogs/measurements
│   └── papers/        # Publications and drafts
```

### `/arc/home/username/` - Personal Space

**✅ Use for:**

- Personal configuration files (`.bashrc`, `.jupyter/`)
- SSH keys and authentication
- Personal scripts and tools
- Small reference files

**❌ Don't use for:**

- Large datasets (limited to 10GB)
- Shared project data
- Temporary processing files

### `/scratch/` - High-Performance Temporary Storage

**✅ Use for:**

- Large intermediate files during processing
- Temporary downloads before moving to `/arc/projects`
- High I/O operations that need maximum speed

**⚠️ Important:**

- **Files are deleted every night at midnight**
- No backup - files can be lost
- Fastest storage available

```bash
# Example: Download large file to scratch, then move to permanent storage
cd /scratch
wget https://archive.example.com/large_dataset.tar.gz
tar -xzf large_dataset.tar.gz
mv processed_data/ /arc/projects/myproject/data/
```

### VOSpace - Long-term Archive

**✅ Use for:**

- Final published datasets
- Data sharing with external collaborators
- Long-term preservation
- Public data releases

**Access methods:**

- Web interface: <https://www.canfar.net/storage/vault/>
- Command line: `vcp`, `vls`, `vmkdir`
- Direct mount: Use VOSpace tools

---

## 📁 Data Transfer Strategies

### Small Files (<1GB)

1. **Web upload** to `/arc/projects/`
   - Use browser file manager
   - Drag and drop interface

### Medium Files (1-100GB)

1. **sshfs mount** for interactive access
2. **VOSpace tools** for reliable transfer
3. **Direct download** in notebook/desktop sessions

### Large Files (>100GB)

1. **Direct download** to `/scratch/` in sessions
2. **Process immediately** and save results to `/arc/projects`
3. **Use command line tools** within sessions

---

## 💽 Storage Management

### Check Current Usage

```bash
# Check project storage usage
df -h /arc/projects/your-group

# Check home directory usage  
df -h /arc/home/$USER

# Check scratch space
df -h /scratch
```

### Quota Information

- **Home directory**: 10GB default (contact support for increases)
- **Project quotas**: Vary by project (100GB to 10TB+)
- **Scratch space**: Unlimited (but temporary)

### Request Quota Increase

Email [support@canfar.net](mailto:support@canfar.net) with:

1. Project name and current usage
2. Justification for additional space
3. Expected data growth timeline

---

## 🔐 Permissions and Sharing

### Default Permissions

- **Home directory**: Only you can access
- **Project directories**: All group members have read/write access
- **Scratch**: Personal space (other users can't access your files)

### Sharing Data

```bash
# Make files readable by group
chmod g+r /arc/projects/myproject/data/dataset.fits

# Make directory accessible
chmod g+x /arc/projects/myproject/data/

# Share with specific permissions
chmod 755 /arc/projects/myproject/shared/
```

---

## 📋 Best Practices

### Data Organization

1. **Use descriptive directory names** with dates/versions
2. **Document data sources** in README files
3. **Keep raw data separate** from processed data
4. **Use consistent naming conventions**

### Backup Strategy

1. **Critical data**: Store in `/arc/projects/` (auto-backed up)
2. **Final results**: Also copy to VOSpace for long-term preservation
3. **Code**: Use version control (git) in addition to file backups
4. **Temporary files**: Keep only in `/scratch/`

### Performance Tips

1. **Use `/scratch/` for I/O intensive processing**
2. **Move final results** to `/arc/projects/` when complete
3. **Clean up old files** regularly to maintain performance
4. **Use appropriate file formats** (HDF5 for large arrays, FITS for astronomy)

---

## 🚨 Troubleshooting

### "No space left on device"

```bash
# Check which filesystem is full
df -h

# Clean up scratch space
rm -rf /scratch/old_files/

# Check project quota
quota -u $USER
```

### "Permission denied"

```bash
# Check file permissions
ls -la /arc/projects/myproject/file.fits

# Fix permissions if you own the file
chmod 644 /arc/projects/myproject/file.fits
```

### "Files disappeared"

```bash
# Check if you're looking in the right place
pwd
ls -la

# Files in /scratch are deleted nightly
# Check /arc/projects/ for permanent files
ls /arc/projects/myproject/
```

---

## 🆘 Getting Help

- **Storage questions**: [support@canfar.net](mailto:support@canfar.net)
- **Usage problems**: [FAQ](help/faq.md)
- **Data transfer**: [Complete transfer guide](data-transfer-guide.md)
- **Project Space Management**: [Project space guide](user-guide/project-space.md) - Setting up collaborative project storage
