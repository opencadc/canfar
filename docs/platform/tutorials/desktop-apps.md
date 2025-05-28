# Desktop Applications and Software Tools

Comprehensive guide to using desktop applications and specialized astronomy software on CANFAR.

## 🖥️ Desktop Environment Overview

The CANFAR desktop provides a full Linux environment accessible through your web browser, with pre-installed astronomy software and the ability to run GUI applications.

### Quick Start
1. [Launch Desktop](../general/NewUser/launch-desktop.md) from the portal
2. Wait ~60 seconds for the desktop to load
3. Access applications through the desktop menu or command line

---

## 🔭 Astronomy Software

### CASA (Radio Interferometry)
**Common Astronomy Software Applications** - the standard tool for radio interferometry data reduction.

**Available versions**:
- CASA 6.6 (latest stable)
- CASA 6.5 (previous stable)  
- CASA 6.4 (for legacy scripts)
- CASA 6.1-6.2 (legacy support)

**Getting started**:
1. [Launch Desktop session](../general/NewUser/launch-desktop.md)
2. [Start CASA](../general/ALMA_Desktop/start-casa.md)
3. Follow [ALMA tutorials](../general/ALMA_Desktop/typical-reduction.md)

📹 **Video tutorial**: [CASA Desktop Walkthrough](https://youtu.be/GDDQ3jKbldU)

### DS9 (Image Display)
**SAOImage DS9** - versatile astronomy image display tool.

**Features**:
- FITS image viewing and analysis
- Multi-frame support
- Coordinate systems and overlays
- Photometry and spectral extraction
- Integration with Virtual Observatory tools

**Usage**:
```bash
# Launch DS9 from desktop terminal
ds9 /arc/projects/your-group/data/image.fits &

# Or use from applications menu
```

### TOPCAT (Table Analysis)
**Tool for OPerations on Catalogues And Tables** - interactive graphical viewer for tabular data.

**Features**:
- Large catalog visualization
- Cross-matching between catalogs
- Statistical analysis and plotting
- VO protocol support (TAP, SAMP)
- Custom expression evaluation

**Usage**:
- Find TOPCAT in Applications menu
- Load tables from `/arc/projects/your-group/data/`
- Connect to VO services for external data

---

## 🐍 Programming Environments

### Python Development
The desktop includes multiple Python environments:

**System Python**:
```bash
python3 /path/to/your/script.py
```

**Conda environments**:
```bash
# List available environments
conda env list

# Activate astronomy environment
conda activate astro

# Install packages
conda install -c astroquery
```

**IPython and Jupyter**:
```bash
# Start IPython console
ipython

# Launch Jupyter from desktop
jupyter lab --no-browser --port=8888
```

### R and RStudio
```bash
# R console
R

# RStudio (if available in container)
rstudio &
```

---

## 🛠️ Development Tools

### Text Editors and IDEs

**Vim/Nano**: Command-line editors
```bash
vim /arc/projects/group/script.py
nano /arc/projects/group/notes.txt
```

**Gedit**: Simple graphical editor
- Available in Applications → Accessories

**VS Code**: (In custom containers)
- Full IDE with extensions
- Git integration
- Remote development features

### Version Control
```bash
# Git is pre-installed
git clone https://github.com/youruser/project.git
cd project
git add .
git commit -m "Analysis updates"
git push origin main
```

---

## 💻 Command Line Tools

### System Administration
```bash
# Check system resources
htop
df -h /arc

# Install software (you have sudo)
sudo apt update
sudo apt install package-name

# Check running processes
ps aux | grep python
```

### File Management
```bash
# Navigate project structure
cd /arc/projects/your-group
ls -la data/

# Find files
find . -name "*.fits" -type f
locate filename

# Compress/decompress
tar -czf archive.tar.gz data/
gunzip compressed_file.gz
```

### Network Tools
```bash
# Download data
wget https://archive.example.com/dataset.tar.gz
curl -O https://api.example.com/data.json

# Transfer files
scp file.txt user@server:/path/
rsync -av local/ remote:/backup/
```

---

## 🔬 Specialized Workflows

### Image Processing Pipeline
```bash
# Example astronomy image processing
cd /arc/projects/group/data/

# Use CASA for radio data
casa --nologger -c "importfits('raw.fits', 'calibrated.ms')"

# Use DS9 for inspection
ds9 processed_image.fits &

# Python analysis
python analysis_script.py processed_image.fits
```

### Data Reduction Workflow
1. **Load raw data** into appropriate software (CASA, DS9)
2. **Apply calibrations** using standard procedures
3. **Export processed data** to `/arc/projects/group/results/`
4. **Generate plots** for quality assessment
5. **Save analysis scripts** for reproducibility

---

## 🎨 Graphical Applications

### X11 Forwarding
GUI applications work seamlessly in the browser-based desktop:
- Full window management
- Copy/paste between applications
- File dialogs access `/arc` storage
- Multi-monitor support (within browser window)

### Performance Optimization
- **Close unused applications** to free memory
- **Use terminal versions** when possible for better performance
- **Adjust desktop resolution** if interface seems slow
- **Monitor resource usage** with `htop`

---

## 📁 File Integration

### Desktop File Manager
- **Nautilus/Thunar**: Graphical file browser
- **Direct access**: to `/arc/home` and `/arc/projects`
- **Integration**: with applications for open/save dialogs

### Application Data Paths
```bash
# Application configs (persistent across sessions)
~/.casa/          # CASA settings
~/.ds9/           # DS9 preferences  
~/.jupyter/       # Jupyter configuration
~/.bashrc         # Shell customization

# Project data (shared with team)
/arc/projects/group/data/      # Input datasets
/arc/projects/group/results/   # Analysis outputs
/arc/projects/group/scripts/   # Analysis code
```

---

## 🔧 Customization

### Desktop Environment
```bash
# Customize shell
echo 'alias ll="ls -la"' >> ~/.bashrc
echo 'export EDITOR=vim' >> ~/.bashrc

# Desktop shortcuts
cp /usr/share/applications/casa.desktop ~/Desktop/
chmod +x ~/Desktop/casa.desktop
```

### Application Settings
- **CASA**: Customize startup scripts in `~/.casa/init.py`
- **DS9**: Save preferred settings and regions
- **Python**: Install personal packages with `pip install --user`

---

## 🚨 Troubleshooting

### Common Issues

**Application won't start**:
```bash
# Check if process is running
ps aux | grep application-name

# Try starting from terminal for error messages
application-name &

# Check system resources
free -h
df -h
```

**Display problems**:
- Refresh browser page
- Try different browser (Chrome/Firefox work best)
- Check internet connection stability

**Performance issues**:
- Close unnecessary applications
- Restart the session if memory is low
- Use command-line versions when possible

### Getting Help
- **Desktop issues**: [Desktop documentation](../general/NewUser/launch-desktop.md)
- **CASA problems**: [CASA container notes](../general/ALMA_Desktop/casa-containers.md)
- **General support**: [Slack channel](https://cadc.slack.com/archives/C01K60U5Q87)

---

## 💡 Pro Tips

### Productivity
- **Learn keyboard shortcuts**: Speed up common tasks
- **Use screen/tmux**: For persistent terminal sessions
- **Organize workspaces**: Keep related applications together
- **Save frequently**: Desktop sessions can be renewed but applications may crash

### Collaboration
- **Document your setup**: Share application configurations
- **Use shared scripts**: Store reusable code in `/arc/projects/group/scripts/`
- **Standardize environments**: Consider custom containers for team consistency

### Resource Management
- **Monitor usage**: Keep an eye on CPU and memory
- **Clean up files**: Remove temporary data regularly
- **Optimize workflows**: Use appropriate tools for each task

The desktop environment provides the flexibility of a full Linux workstation with the convenience of browser access and shared storage!
