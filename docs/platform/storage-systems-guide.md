# CANFAR Storage Systems Guide

> **📚 Related Guides:**
>
> - [Complete Data Transfer Methods →](data-transfer-guide.md) - How to move files to/from each storage system
> - [Container Building Guide →](container-building-guide.md) - Storage access in custom containers
> - [Headless Execution Guide →](headless-execution-guide.md) - Storage usage in batch processing
> - [Getting Started: Choose Interface →](getting-started/choose-interface.md) - Interface overview

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
```
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
└── docs/
    ├── README.md      # Project documentation
    └── protocols/     # Analysis procedures
```

### `/arc/home/username/` - Personal Space
**✅ Use for:**
- Personal configuration files (`.bashrc`, `.jupyter/`)
- SSH keys and certificates
- Personal software installations
- Private notes and drafts

**❌ Don't use for:**
- Large datasets (limited to 10GB)
- Files you want to share with team

### `/scratch/` - High-Performance Temporary Storage
**✅ Use for:**
- Large intermediate files during processing
- Temporary downloads from archives
- Working space for computationally intensive tasks
- Any files you can recreate if lost

**⚠️ Important:**
- **Files are deleted every night at midnight**
- No backups - treat as completely temporary
- Fastest storage available (NVMe SSDs)
- No quota limits

**Example workflow:**
```bash
# Download large archive to scratch for processing
cd /scratch
wget https://archive.example.com/largefile.tar.gz

# Process data in scratch (fast I/O)
tar xzf largefile.tar.gz
process_data largefile/ --output processed/

# Copy results to permanent storage
cp -r processed/ /arc/projects/myproject/results/
```

### VOSpace - Long-term Archive
**✅ Use for:**
- Final published datasets
- Data for sharing with broader community
- Long-term preservation (years to decades)
- Compliance with data sharing requirements

**Access methods:**
- Web interface: <https://www.canfar.net/storage/vault/>
- Command line: `vcp`, `vls`, `vmkdir` tools
- From sessions: Limited (use for final uploads)

## 🔄 Data Movement Strategies

### Small Files (<1GB)
1. **Web upload** to `/arc/projects/`
2. **Notebook upload** for immediate use
3. **Direct editing** in sessions

### Medium Files (1-100GB)
1. **sshfs mount** for interactive access
2. **VOSpace tools** for reliable transfer
3. **Direct download** to sessions

### Large Files (>100GB)
1. **Direct download** to `/scratch/` in sessions
2. **Process in place** on high-speed storage
3. **Move results** to `/arc/projects/`

## 💾 Storage Quotas and Monitoring

### Check Current Usage
```bash
# Check project storage usage
df -h /arc/projects/yourproject

# Detailed breakdown by directory
du -sh /arc/projects/yourproject/*

# Check home directory usage
df -h /arc/home/yourusername
```

### Quota Information
- **Project quotas**: Vary by project (100GB to 10TB+)
- **Home quota**: 10GB default (can be increased)
- **File count limits**: Usually generous for astronomy data
- **Backup retention**: 30 days for deleted files

### Request Quota Increase
Email [support@canfar.net](mailto:support@canfar.net) with:
1. Project name and current usage
2. Requested new quota size
3. Scientific justification
4. Timeline for data usage

## 🔒 Permissions and Sharing

### Default Permissions
- **Home directory**: Only you can access
- **Project directories**: All group members have read/write
- **Subdirectories**: Inherit parent permissions

### Sharing Data
```bash
# Make directory readable by group
chmod g+r /arc/projects/myproject/shared_data/

# Make scripts executable for group
chmod g+x /arc/projects/myproject/scripts/*.py

# Check permissions
ls -la /arc/projects/myproject/
```

## 🚨 Best Practices

### Data Organization
1. **Use descriptive directory names** with dates/versions
2. **Keep README files** explaining data sources and processing
3. **Version control** for code (git repositories)
4. **Regular cleanup** of temporary and intermediate files

### Backup Strategy
1. **Critical data**: Store in `/arc/projects/` (auto-backed up)
2. **Final results**: Also archive to VOSpace
3. **Code**: Use GitHub/GitLab in addition to CANFAR storage
4. **Large datasets**: Document data sources for re-download if needed

### Performance Tips
1. **Use `/scratch/` for I/O intensive processing**
2. **Minimize small file operations** on shared storage
3. **Compress large datasets** when not actively used
4. **Use appropriate file formats** (HDF5, Parquet) for large tables

## 🆘 Troubleshooting

### Common Issues

**"No space left on device"**
```bash
# Check which filesystem is full
df -h
# Clean up temporary files or request quota increase
```

**"Permission denied"**
```bash
# Check file permissions
ls -la filename
# Check group membership
groups
```

**"Files disappeared"**
```bash
# Check if you're in the right directory
pwd
# Look in backup directory (contact support)
# Check /scratch/ - files are deleted nightly
```

### Getting Help
- **Storage questions**: [support@canfar.net](mailto:support@canfar.net)
- **Permission issues**: [Slack #canfar-support](https://cadc.slack.com/archives/C01K60U5Q87)
- **Data transfer help**: See [Complete Transfer Guide](data-transfer-guide.md)

---

**Related Documentation:**

- [Complete Data Transfer Guide](data-transfer-guide.md) - All methods to move data to/from storage systems
- [Container Building Guide](container-building-guide.md) - Storage access patterns in custom containers  
- [Headless Execution Guide](headless-execution-guide.md) - Storage usage in batch processing workflows
- [Getting Started: Choose Interface](getting-started/choose-interface.md) - Interface overview for new users
- [Project Space Management](general/NewUser/project-space.md) - Setting up collaborative project storage
