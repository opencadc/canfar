# Using Desktop Applications in CANFAR

Guide to running graphical desktop applications in your CANFAR Desktop sessions, from basic tools to specialized astronomy software.

## 📋 Overview

CANFAR Desktop sessions provide a full Linux desktop environment with access to a wide range of scientific applications. This tutorial covers how to find, launch, and use desktop applications effectively.

## 🎯 Prerequisites

- **Desktop session running** - Follow the [Desktop launch guide](../user-guide/launch-desktop.md)
- **Basic familiarity** with Linux desktop environments

## 🚀 Available Applications

### Core System Applications

**File Management**:
- **File Manager** - Browse and organize files
- **Archive Manager** - Create and extract compressed files

**Text Editing**:
- **Text Editor (gedit)** - Simple text editing
- **LibreOffice** - Full office suite (Writer, Calc, Impress)

**Web Browsing**:
- **Firefox** - Web browser with full internet access

**System Tools**:
- **Terminal** - Command-line interface
- **System Monitor** - View resource usage
- **Calculator** - Basic calculations

### Astronomy Software

**Radio Astronomy**:
- **CASA** - All versions from 3.4.0 to current
- **ADMIT** - Analysis toolkit for ALMA data

**Optical/IR Astronomy**:
- **IRAF** - Image Reduction and Analysis Facility
- **DS9** - Astronomical image viewer
- **Astropy-based tools** - Python astronomy libraries

**Data Analysis**:
- **Python IDEs** - Spyder, VS Code
- **Jupyter Lab** - Interactive notebooks
- **R/RStudio** - Statistical analysis

## 🖱️ Launching Applications

### Method 1: Applications Menu

1. **Click Applications** - Located in the top-left corner of your desktop
2. **Browse categories** - Navigate through organized application folders:
   - **AstroSoftware** - Astronomy-specific applications
   - **Office** - LibreOffice suite
   - **Internet** - Firefox and web tools
   - **Accessories** - Basic utilities
   - **System Tools** - Administrative applications

3. **Select application** - Click on the desired application to launch

### Method 2: Quick Launch Icons

Common applications have **quick launch icons** on the desktop taskbar:
- **Terminal** - Command-line access
- **File Manager** - File browser
- **Firefox** - Web browser
- **Text Editor** - Simple text editing

### Method 3: Command Line

Launch applications from a terminal:

```bash
# Launch graphical applications
firefox &
gedit &
libreoffice &

# Launch astronomy software
ds9 &
casa &
```

**💡 Tip**: The `&` runs applications in the background, allowing you to continue using the terminal.

## 🔬 Astronomy Software Usage

### CASA (Radio Astronomy)

**Multiple versions available**:
- Navigate: **Applications → AstroSoftware → CASA → [Version]**
- Choose specific version based on your data requirements
- See [CASA tutorial](start-casa.md) for detailed instructions

### DS9 (Image Viewer)

**Launch DS9**:
```bash
# From terminal
ds9 &

# Or from Applications → AstroSoftware → DS9
```

**Basic usage**:
- **Load images**: File → Open, or drag and drop FITS files
- **Adjust display**: Use scale, colormap, and zoom controls
- **Multi-frame**: Load multiple images for comparison
- **Coordinate systems**: Display various coordinate grids

### IRAF

**Launch IRAF**:
```bash
# Set up IRAF environment
mkiraf
iraf &
```

**What this does**: Creates necessary IRAF configuration files and launches the interactive environment.

## 📁 Working with Files

### File Manager Features

**Navigation**:
- **Bookmarks**: Quick access to frequently used directories
- **Location bar**: Type paths directly (Ctrl+L)
- **Split view**: View two directories simultaneously

**File operations**:
- **Copy/paste**: Standard Ctrl+C, Ctrl+V shortcuts
- **Drag and drop**: Move files between directories
- **Right-click menu**: Context-sensitive options

### Opening Files in Applications

**Double-click behavior**:
- **Text files** → Text Editor
- **FITS files** → DS9 (if configured)
- **PDF files** → Document viewer
- **Images** → Image viewer

**Custom associations**:
```bash
# Set DS9 as default for FITS files
# Right-click FITS file → Properties → Open With → Choose DS9
```

## 🎨 Desktop Customization

### Window Management

**Organizing windows**:
- **Maximize**: Double-click title bar
- **Minimize**: Click minimize button
- **Move**: Drag title bar
- **Resize**: Drag window edges/corners

**Virtual desktops**:
- Use **workspace switcher** to organize applications
- Move applications between workspaces
- Create focused work environments for different tasks

### Display Settings

**Adjust resolution**:
- **Applications → System Tools → Settings**
- **Select Display** settings
- **Choose resolution** that works best for your screen

### Theme and Appearance

**Customize appearance**:
- **Applications → System Tools → Settings**
- **Select Appearance** or **Theme**
- **Adjust** colors, fonts, and window decorations

## 📊 Performance Optimization

### Resource Management

**Monitor usage**:
```bash
# Check CPU and memory usage
top

# Or use graphical system monitor
# Applications → System Tools → System Monitor
```

**Close unused applications**:
- Close applications you're not actively using
- Use **Alt+Tab** to switch between running applications
- **Ctrl+Alt+T** for quick terminal access

### Application-Specific Tips

**Firefox**:
- **Close unused tabs** to save memory
- **Disable unnecessary plugins** for better performance
- **Use private browsing** for temporary sessions

**CASA**:
- **Close CASA completely** when switching versions
- **Monitor memory usage** for large datasets
- **Use appropriate image display settings**

**File operations**:
- **Use command line** for bulk file operations
- **Compress large files** before transferring
- **Organize files** to avoid cluttered directories

## 🚨 Troubleshooting

### Application Won't Start

```bash
# Check if application is installed
which application_name

# Try launching from terminal to see error messages
application_name

# Check system resources
free -h
df -h
```

### Graphics Issues

**Display problems**:
- **Refresh desktop**: Right-click desktop → Refresh
- **Restart session**: If graphics become corrupted
- **Check browser compatibility**: Some browsers handle VNC better than others

**Slow graphics**:
- **Reduce color depth**: Use 16-bit color if 24-bit is slow
- **Close unnecessary windows**: Reduce graphical load
- **Disable animations**: In system settings

### Application Crashes

**Recovery steps**:
1. **Save work frequently** in case of crashes
2. **Use terminal to kill** hung applications:
   ```bash
   killall application_name
   ```
3. **Restart application** and try again
4. **Check logs** if available:
   ```bash
   tail -f ~/.xsession-errors
   ```

### File Association Problems

```bash
# Reset file associations
# Right-click file → Properties → Open With → Reset to Default

# Or set manually
# Right-click file → Properties → Open With → Choose Application
```

## 💡 Best Practices

### Workflow Organization

**Use virtual desktops**:
- **Desktop 1**: File management and general tasks
- **Desktop 2**: Data analysis (CASA, Python)
- **Desktop 3**: Documentation and research (Firefox, LibreOffice)

**Keep terminals organized**:
- **Label terminal windows** for different purposes
- **Use screen or tmux** for persistent sessions
- **Keep CASA terminals** separate from general terminals

### Data Management

**Save work regularly**:
- **Auto-save** in applications when available
- **Version control** for scripts and analysis
- **Backup important results** to permanent storage

**File organization**:
```bash
# Recommended structure
/arc/projects/yourproject/
├── data/           # Raw and processed data
├── scripts/        # Analysis scripts
├── results/        # Final outputs
├── documents/      # Papers, presentations
└── scratch/        # Temporary files
```

## 🔗 Related Documentation

- **[Desktop session guide](../user-guide/launch-desktop.md)** - Setting up your workspace
- **[CASA tutorial](start-casa.md)** - Detailed CASA usage
- **[File management guide](../user-guide/web-file-manager.md)** - Working with files
- **[Storage systems guide](../storage-systems-guide.md)** - Understanding CANFAR storage
- **[Data transfer guide](../data-transfer-guide.md)** - Moving files efficiently

**External Resources**:
- [DS9 User Manual](http://ds9.si.edu/doc/user/)
- [CASA Documentation](https://casadocs.readthedocs.io/)
- [IRAF User Guide](http://iraf.noao.edu/docs/)