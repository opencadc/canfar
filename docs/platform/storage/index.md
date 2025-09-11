# Storage Systems

**CANFAR's storage systems: choosing the right storage, understanding how sessions interact with storage, and optimising your data workflows.**

!!! abstract "🎯 Storage Guide"
    **Master CANFAR's storage systems:**
    
    - **[Filesystem Access](filesystem.md)**: ARC storage, SSHFS mounting, and permissions
    - **[Data Transfers](transfers.md)**: Moving data between systems and external sources  
    - **[VOSpace Guide](vospace.md)**: Long-term storage, sharing, and archival
    - **Storage Strategy**: Choosing optimal storage for your workflows

CANFAR provides four distinct storage systems, each optimised for different stages of the research lifecycle. Understanding how these systems work together with CANFAR sessions is essential for efficient data management and analysis workflows.

## 📊 Storage Types

| Storage Type    | Location/URI | Access Speed | Visibility | Persistence | Backup | Session Access | Best For |
|----------------|--------------|--------------|------------|-------------|--------|----------------|----------|
| **Scratch**     | `/scratch/` | Fastest SSD | Session only | ❌ Wiped at end | ❌ None | Direct filesystem | High-speed temporary processing |
| **ARC Home**    | `/arc/home/[user]/` | Shared CephFS | Personal | ✅ Permanent | ✅ Daily snapshots | Direct filesystem | Personal configs, scripts, small files |
| **ARC Projects** | `/arc/projects/[project]/` | Shared CephFS | Shared group | ✅ Permanent | ✅ Daily snapshots | Direct filesystem | Active collaborative research |
| **Vault**       | `vos:[project\|user]/` | Medium | Personal/shared | ✅ Permanent | ✅ Geo-redundant | API/Web only | Long-term archives, data sharing |

## 🔄 How Sessions Use Storage

CANFAR sessions (interactive containers, batch jobs) integrate with storage systems in different ways:

### Direct Filesystem Access (Inside Sessions)

```bash
# Sessions automatically mount ARC storage as standard directories
ls /arc/home/[user]/            # Your personal space
ls /arc/projects/[project]/     # Shared project space  
ls /scratch/                    # Temporary fast storage

# Standard Unix commands work directly
cp /arc/projects/[project]/data.fits /scratch/
python analysis.py /scratch/data.fits
mv results.png /arc/projects/[project]/figures/
```

### Session Storage Workflow

```mermaid
graph TD
    Start([Session Starts]) --> Mount[ARC Storage Auto-mounted]
    Mount --> Scratch[Empty /scratch/ Created]
    Scratch --> Work[Work with Data]
    Work --> Save[Save Important Results to ARC]
    Save --> End([Session Ends])
    End --> Cleanup[/scratch/ Wiped Clean]
    
    Work --> Process{Large Processing?}
    Process -->|Yes| UseScratch[Use /scratch/ for speed]
    Process -->|No| UseARC[Work directly in ARC]
    
    UseScratch --> Save
    UseARC --> Save
```

## 🎯 Storage Selection Guide

### By Workflow Type

#### Interactive Analysis Sessions

- **Start in**: `/arc/projects/[project]/` (your data)
- **Process in**: `/scratch/` (large temporary files)  
- **Save to**: `/arc/projects/[project]/results/` (permanent results)

#### Batch Processing Jobs

- **Input from**: Vault (long-term storage) or ARC Projects
- **Process in**: `/scratch/` (fastest I/O)
- **Output to**: ARC Projects (shared results) or Vault (archives)

#### Data Sharing & Collaboration

- **Active work**: ARC Projects (group members)
- **External sharing**: Vault (public URLs, fine-grained permissions)
- **Personal tools**: ARC Home (configurations, scripts)

### By Data Size and Type

=== "Small Files (<1GB)"
    - **Personal scripts/configs**: ARC Home
    - **Shared analysis code**: ARC Projects  
    - **Quick processing**: Direct in ARC (no need for scratch)

=== "Medium Files (1-100GB)"
    - **Raw datasets**: ARC Projects or Vault
    - **Processing**: Copy to `/scratch/`, process, save results to ARC
    - **Results**: ARC Projects for sharing, Vault for archival

=== "Large Files (>100GB)"  
    - **Storage**: Vault (geo-redundant) or ARC Projects (faster access)
    - **Processing**: Always use `/scratch/` for performance
    - **Strategy**: Process in chunks, stream results to permanent storage

## 🚀 Performance Optimization

### Storage Speed Hierarchy

```text
/scratch/           ← Fastest (local SSD)
/arc/projects/      ← Shared CephFS (Network)
/arc/home/          ← Shared CephFS (Network)
vos: (Vault)        ← Medium (Network)
```

### Optimal Data Flow Patterns

#### Pattern 1: Large Dataset Analysis

```bash
# 1. Stage data from slow to fast storage
vcp vos:project/bigdata.fits /scratch/           # Vault → Scratch
# or
cp /arc/projects/[project]/bigdata.fits /scratch/  # ARC → Scratch

# 2. Process on fastest storage  
casa_analysis.py /scratch/bigdata.fits           # Work in scratch

# 3. Save results to permanent storage
cp /scratch/results/* /arc/projects/[project]/   # Scratch → ARC
```

#### Pattern 2: Collaborative Workflow

```bash
# Team member A prepares data
cp raw_observations.fits /arc/projects/[project]/data/

# Team member B processes  
cp /arc/projects/[project]/data/raw_observations.fits /scratch/
run_pipeline.py /scratch/raw_observations.fits
cp processed_data.fits /arc/projects/[project]/processed/

# Team member C analyzes results
python analyze.py /arc/projects/[project]/processed/processed_data.fits
```

#### Pattern 3: Archive and Share

```bash
# Work actively in ARC Projects
python long_analysis.py /arc/projects/[project]/

# Archive final results to Vault
vcp /arc/projects/[project]/final_paper_data/ vos:[user]/publications/

# Share with external collaborators via Vault
vchmod o+r vos:[user]/publications/shared_catalogue.fits
```

## 📈 Quota Management

### Default Quotas

- **ARC Home**: 10GB (personal files only)
- **ARC Projects**: 200GB (can be increased)
- **Scratch**: ~100GB (temporary only)
- **Vault**: Project-dependent (request from support)

### Monitoring Usage

```bash
# Check ARC storage usage
df -h /arc/home/[user]/
df -h /arc/projects/[project]/

# Detailed breakdown
du -sh /arc/projects/[project]/*

# Check Vault usage via web interface
# Visit: https://www.canfar.net/storage/vault/list/
```

### Requesting Increases

Contact CANFAR support (`support@canfar.net`) with:

- Project name and current usage
- Estimated additional space needed
- Justification (dataset size, collaboration needs)
- Timeline for the project

## 🔗 Integrations

### Session Types and Storage Access

| Session Type | ARC Access | Vault Access | Scratch | Best For |
|--------------|------------|--------------|---------|----------|
| **Notebook** | ✅ Direct filesystem | ✅ VOSpace API | ✅ Direct | Interactive analysis |
| **Desktop** | ✅ Direct filesystem | ✅ VOSpace API | ✅ Direct | GUI applications |
| **CARTA** | ✅ Direct filesystem | ✅ VOSpace API | ✅ Direct | Interactive visualization |
| **Firefly** | ✅ Direct filesystem | ✅ VOSpace API | ✅ Direct | Interactive catalogue queries |
| **Contributed** | ✅ Direct filesystem | ✅ VOSpace API | ✅ Direct | Many, e.g. code development |
| **Batch Jobs** | ✅ Direct filesystem | ✅ VOSpace API | ✅ Direct | Automated processing |
| **External (via SSH)** |  ⚠️ SSHFS mount | ✅ VOSpace API | ❌ Not available | Remote access |

### Authentication and Permissions

- **ARC storage**: Automatic within sessions, SSHFS for external access, also requires CADC certificate if using the VOSpace `arc:`
- **Vault**: Requires CADC certificate (`cadc-get-cert`)
- **Group permissions**: Managed via CANFAR Group Management tools

## ❓ Troubleshooting

**"No space left on device" in ARC Home**

```bash
# Check usage and clean up
du -sh /arc/home/[user]/*
rm -rf /arc/home/[user]/large_old_files/
```

**Can't access project directory**

- Verify you're a member of the project group
- Contact project PI to add you to the group

**Session performance issues**

- Move large files from ARC to `/scratch/` for processing
- Use `/scratch/` for temporary files and intensive I/O operations

**Files disappeared after session**

- Check if files were saved to `/scratch/` (wiped at session end)
- Always save important results to `/arc/` or Vault before ending session
