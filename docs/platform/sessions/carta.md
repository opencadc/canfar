# CARTA Sessions

**CARTA (Cube Analysis and Rendering Tool for Astronomy) for astronomy data visualisation**

!!! abstract "🎯 What You'll Learn"
    - How to launch CARTA sessions and choose the right version
    - Loading data from CANFAR storage and working with radio data cubes
    - Key features for spectral analysis, region analysis, and animations
    - Performance tips and troubleshooting guidance

CARTA is a specialised image visualisation and analysis tool designed specifically for radio astronomy data. It excels at handling multi-dimensional data cubes, providing powerful tools for spectral analysis, and enabling real-time collaborative workflows.

## 📋 Overview

CARTA provides specialised capabilities for:

### Key Features

| Feature | Capability |
|---------|------------|
| **Image Visualisation** | Multi-dimensional data cube exploration with WCS support |
| **Spectral Analysis** | Line profiles, moment maps, and velocity analysis |
| **Region Analysis** | Statistical analysis of user-defined image regions |
| **Animation** | Time-series and frequency animations through data cubes |
| **Collaboration** | Real-time session sharing with multiple users |
| **Performance** | Optimised rendering for large astronomical datasets |

### Data Format Support

- **FITS files:** Standard astronomical format with full WCS support
- **HDF5 files:** High-performance format for large datasets
- **CASA images:** Native support for CASA image formats
- **Compressed formats:** Automatic handling of gzipped files

## 🚀 Creating a CARTA Session

### Step 1: Select Session Type

From the Science Portal dashboard, click the **plus sign (+)** to create a new session, then select **carta** as your session type.

### Step 2: Choose Container Version

Note that the menu options update automatically after your session type selection. Choose the CARTA version that meets your needs:

#### Available Versions

- **CARTA 4.0** (recommended): Latest features and bug fixes
- **CARTA 3.x:** Previous stable releases for compatibility

!!! tip "Version Selection"
    Use the latest version (4.0+) unless you specifically need compatibility with older workflows. New versions include performance improvements and additional features.

### Step 3: Configure Session

#### Session Name

Choose a descriptive session name to help you identify it later:

**Good session names:**
- `m87-analysis`
- `ngc-1300-cube`
- `alma-co-line-study`
- `vla-continuum-imaging`

#### Resource Allocation

Start with a "flexible" session for most analyses. Switch to a fixed resource allocation if you need guaranteed performance for demanding visualisations.

**Resource Guidelines:**
- **Flexible:** Good for most CARTA workflows
- **Fixed:** Use for large datasets (>1GB) or guaranteed performance

### Step 4: Launch Session

Click the **Launch** button and wait for your session to initialise. CARTA sessions typically start within 30-60 seconds.

## 🧭 Using CARTA

### First Steps

Once connected to your CARTA session:

1. **File Menu:** Use "Open Image" to load your data
2. **File Browser:** Navigate to `/arc/projects/[project]/` or `/arc/home/[user]/`
3. **Load Data:** Select FITS or HDF5 files to visualise

### Data Loading

#### From CANFAR Storage

```bash
# CARTA can access files from:
/arc/home/[user]/                    # Your personal data
/arc/projects/[project]/             # Shared project data
/scratch/                            # Temporary high-speed storage
```

#### Supported File Paths

- **Local files:** Any file accessible in the session filesystem
- **Remote files:** HTTP/HTTPS URLs (limited support)
- **Archive data:** Files downloaded to CANFAR storage

### Interface Overview

#### Main Components

- **Image Viewer:** Central panel showing the astronomical image
- **File Browser:** Left panel for navigating and opening files
- **Region List:** Panel for managing analysis regions
- **Statistics:** Real-time statistics for selected regions
- **Spectral Profiler:** Panel for line profile analysis
- **Animation:** Controls for cycling through cube slices

#### Essential Controls

| Control | Function |
|---------|----------|
| **Mouse wheel** | Zoom in/out |
| **Click + drag** | Pan around image |
| **Right-click** | Context menu with additional options |
| **Keyboard shortcuts** | See Help menu for complete list |

## 🔬 Analysis Features

### Spectral Analysis

#### Line Profiles

1. **Draw regions** on the image
2. **Open Spectral Profiler** panel
3. **Select region** to view spectrum
4. **Analyse lines** with built-in fitting tools

#### Moment Maps

CARTA can generate:

- **Moment 0:** Integrated intensity
- **Moment 1:** Velocity field  
- **Moment 2:** Velocity dispersion

### Region Analysis

#### Creating Regions

1. **Select region tool** from toolbar
2. **Draw on image:** Rectangle, ellipse, polygon, or point
3. **View statistics** in the Statistics panel
4. **Export regions** in DS9 or CRTF format

#### Statistical Analysis

CARTA automatically computes:
- **Sum, mean, RMS** within regions
- **Min/max values** and positions
- **Flux measurements** with proper units
- **Histogram analysis** of pixel values

### Animation and Navigation

#### Data Cube Navigation

- **Slider controls:** Navigate through spectral channels or Stokes parameters
- **Animation playback:** Automatic cycling through cube slices
- **Frame rate control:** Adjust animation speed
- **Custom ranges:** Focus on specific velocity ranges

#### Multi-Panel Views

- **Compare datasets:** Load multiple images simultaneously
- **Linked panels:** Synchronise zoom, pan, and navigation
- **Layout control:** Arrange panels as needed

## ⚡ Performance Optimisation

### Large Dataset Handling

#### Memory Management

```bash
# Monitor session resources
htop                    # Check memory usage
df -h                   # Check disk space
```

#### Optimisation Tips

- **Use /scratch for large files:** Copy data to high-speed storage
- **Close unused files:** Reduce memory consumption
- **Reduce image resolution:** For initial exploration
- **Use data subsets:** Work with spatial/spectral sub-cubes

### Network Performance

#### For Remote Access

- **Stable connection:** CARTA requires consistent network connectivity
- **Bandwidth:** Higher bandwidth improves responsiveness
- **Close other applications:** Reduce network competition

## 🤝 Collaboration Features

### Real-Time Sharing

CARTA supports collaborative analysis:

1. **Share session URL** with team members
2. **Simultaneous access:** Multiple users can connect
3. **Synchronised views:** All users see the same state
4. **Coordinate activities:** Communicate to avoid conflicts

### Best Practices for Collaboration

- **Designate a lead:** Have one person control navigation
- **Use voice/chat:** Coordinate complex operations
- **Save work frequently:** Export regions and analysis results
- **Plan sessions:** Organise collaborative time in advance

## 🔧 Advanced Features

### Scripting and Automation

#### Export Capabilities

- **Image exports:** PNG, JPEG, PDF formats
- **Region files:** DS9 or CRTF format for other tools
- **Spectral data:** CSV format for further analysis
- **Session state:** Save and restore CARTA configurations

#### Integration with Other Tools

```python
# Load CARTA regions in Python
from astropy.io import fits
from regions import Regions

# Read CARTA-exported region file
regions = Regions.read('carta_regions.crtf', format='crtf')

# Use with other astronomy software
```

### Custom Colour Maps

- **Built-in maps:** Scientific colour schemes
- **Custom maps:** Import your own colour tables
- **Accessibility:** Colour-blind friendly options
- **Publication quality:** High-contrast options for papers

## 🔧 Troubleshooting

### Common Issues

#### Session Won't Load Data

**Problem:** CARTA cannot open FITS files

**Solutions:**

1. Check file permissions and location
2. Verify file format is supported
3. Try copying file to `/scratch/` first
4. Check file isn't corrupted

#### Slow Performance

**Problem:** CARTA responds slowly to interactions

**Solutions:**

1. Check available memory with `htop`
2. Close other browser tabs/applications
3. Reduce image size or use sub-cubes
4. Restart session if memory is exhausted

#### Connection Issues

**Problem:** Lost connection to CARTA session

**Solutions:**

1. Refresh browser page
2. Check internet connection stability
3. Clear browser cache if persistent
4. Try different browser

#### Display Problems

**Problem:** Images don't render correctly

**Solutions:**

1. Try different browser (Chrome/Firefox recommended)
2. Update browser to latest version
3. Disable browser extensions temporarily
4. Check graphics drivers on local machine

