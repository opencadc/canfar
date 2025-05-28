# Understanding Storage

CANFAR uses a shared file system that's accessible from all your sessions. Understanding the storage structure is key to effective collaboration.

## Storage Structure

```
/arc/
├── home/
│   └── your-username/          ← Your private space
│       ├── .bashrc            ← Personal shell configuration  
│       ├── .jupyter/          ← Jupyter settings
│       └── personal-files/    ← Private files and configs
└── projects/
    └── your-group-name/       ← Shared project space
        ├── data/              ← Raw datasets
        ├── scripts/           ← Analysis code
        ├── results/           ← Output files
        └── docs/              ← Documentation
```

## The Two Main Areas

### 🏠 `/arc/home/username` - Your Private Space

**Purpose**: Personal configuration and private files

**What to store here**:
- Shell configuration files (`.bashrc`, `.profile`)
- Personal software installations
- SSH keys and credentials  
- Private notes and drafts

**Key features**:
- ✅ Only you can read/write
- ✅ Backed up regularly
- ✅ Available in all sessions
- ❌ Not shared with collaborators

### 🤝 `/arc/projects/groupname` - Shared Project Space

**Purpose**: Collaboration and shared data

**What to store here**:
- Research datasets
- Analysis scripts and code
- Results and plots
- Shared documentation
- Published workflows

**Key features**:
- ✅ Shared with group members
- ✅ Backed up regularly  
- ✅ Available in all sessions
- ✅ Can set fine-grained permissions

## Best Practices

### 📁 Organizing Project Data

```
/arc/projects/your-group/
├── data/
│   ├── raw/              ← Original, unmodified datasets
│   ├── processed/        ← Cleaned/calibrated data
│   └── external/         ← Data from other sources
├── code/
│   ├── notebooks/        ← Jupyter notebooks
│   ├── scripts/          ← Python/shell scripts  
│   └── pipelines/        ← Complete workflows
├── results/
│   ├── figures/          ← Plots and images
│   ├── tables/           ← Output catalogs/tables
│   └── reports/          ← Analysis summaries
└── docs/
    ├── README.md         ← Project overview
    ├── data-sources.md   ← Data documentation
    └── methods.md        ← Analysis methods
```

### 🔒 File Permissions

By default:
- **Your home directory**: Only you can access
- **Project directories**: All group members can read/write
- **Subdirectories**: Inherit parent permissions (can be customized)

[**→ Learn More About Permissions**](../advanced/permissions.md)

## Accessing Storage

### 📂 Web Interface
[**CANFAR File Manager**](https://www.canfar.net/storage/arc/list) - Browse and manage files in your browser

### 💻 From Your Local Computer
- **sshfs**: Mount storage as local drive ([setup guide](../general/General_tools/Using_sshfs.md))
- **VOSpace tools**: Command-line file transfer ([documentation](../general/General_tools/Using_vostools.md))
- **Web transfers**: Upload/download via browser ([guide](../general/General_tools/File_transfers.md))

### 🔧 Programmatic Access
- **Python VOSpace library**: For scripts and automation
- **REST API**: Direct HTTP access to files
- **From sessions**: Direct file system access at `/arc/`

## Storage Quotas

Your collaboration has:
- **Storage limit**: Typically 100GB - 10TB (varies by project)
- **File count limit**: Usually generous for astronomy data
- **Backup retention**: 30 days for deleted files

Check current usage:
```bash
# In any session
df -h /arc/projects/your-group
```

## What's Next?

Now you're ready to start your first session:

[**→ Launch Your First Session**](choose-interface.md){ .md-button }

---

## Quick Tips

### 💡 Pro Tips
- Use `/arc/projects` for anything you want to share or collaborate on
- Keep personal configs in `/arc/home` so they persist across sessions  
- Organize data logically - your future self will thank you
- Document your data sources and methods in README files

### ⚠️ Important Notes
- Files are **not automatically synced** to your local computer
- **Large datasets** should stay in `/arc/projects` - don't download unnecessarily
- **Sensitive data** should have appropriate permissions set

### 🆘 Need Help?
- **Storage questions**: [support@canfar.net](mailto:support@canfar.net)
- **Permission issues**: [Slack channel](https://cadc.slack.com/archives/C01K60U5Q87)
- **File transfer help**: [File transfer guide](../general/General_tools/File_transfers.md)
