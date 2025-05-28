# Radio Astronomy Workflows

Complete guides for radio astronomy data analysis on CANFAR.

## 🔭 CARTA for Image Analysis

**CARTA** (Cube Analysis and Rendering Tool for Astronomy) is perfect for visualizing and analyzing radio astronomy data.

### Quick Start
1. [Launch CARTA](../general/NewUser/launch-carta.md) from the portal
2. Load your FITS files from `/arc/projects/your-group/data/`
3. Use the built-in analysis tools for measurements

### Common Workflows
- **Data cube visualization**: Navigate through frequency/velocity dimensions
- **Intensity measurements**: Extract flux densities and create profiles
- **Image comparison**: Compare observations at different frequencies
- **Region analysis**: Define and analyze specific sky regions

[**→ Detailed CARTA Tutorial**](../general/NewUser/launch-carta.md){ .md-button }

---

## 🏠 CASA Desktop Workflows

**CASA** (Common Astronomy Software Applications) runs in the desktop environment for complete interferometry data reduction.

### Getting Started
1. [Launch Desktop](../general/NewUser/launch-desktop.md) from the portal
2. Open CASA from the applications menu
3. Access your data in `/arc/projects/your-group/`

### Complete ALMA Workflows
CANFAR has specialized tutorials for ALMA data reduction:

- **[Starting CASA](../general/ALMA_Desktop/start-casa.md)** - Basic setup and configuration
- **[Archive Downloads](../general/ALMA_Desktop/archive-download.md)** - Getting data from ALMA archive  
- **[Script Downloads](../general/ALMA_Desktop/archive-script-download.md)** - Automated data retrieval
- **[Image Reduction](../general/ALMA_Desktop/typical-reduction.md)** - Complete reduction example
- **[CASA Container Notes](../general/ALMA_Desktop/casa-containers.md)** - Known issues and features

### 📹 Video Tutorial
[**CASA Desktop Tutorial**](https://youtu.be/GDDQ3jKbldU) - YouTube walkthrough of launching CASA

---

## 🔄 Typical Radio Workflow

### 1. Data Preparation
```bash
# In desktop terminal
cd /arc/projects/your-group/data/
# Download and organize your datasets
```

### 2. Calibration (CASA)
- Use CASA pipelines for interferometry calibration
- Save calibrated data to `/arc/projects/your-group/data/processed/`

### 3. Imaging (CASA)
- Create images and cubes
- Save products to `/arc/projects/your-group/results/`

### 4. Analysis (CARTA + Notebooks)
- Use CARTA for interactive image analysis
- Switch to Jupyter notebooks for quantitative analysis
- Create publication-quality plots

### 5. Documentation
- Save analysis scripts and methods
- Create summary notebooks for collaboration

---

## 🐳 Available Containers

### CASA Versions
- **CASA 6.6**: Latest stable release
- **CASA 6.5**: Previous stable version  
- **CASA 6.4**: For compatibility with older scripts
- **Custom builds**: Contact support for specific requirements

### CARTA
- **Latest CARTA**: Automatically updated container
- **Stable CARTA**: Fixed version for reproducible analysis

[**→ Container Details**](../complete/available-containers.md){ .md-button }

---

## 📊 Computational Resources

### Typical Requirements
- **Memory**: 8-32 GB RAM for imaging
- **Storage**: 100GB - 10TB for large surveys
- **Compute**: 4-16 cores for pipeline processing

### Optimization Tips
- Use `/arc/projects` for all data - it's optimized for large files
- Save intermediate products to avoid re-computation
- Clean up temporary files to save storage space

---

## 🆘 Getting Help

### Radio Astronomy Support
- **CASA help**: [CASA documentation](https://casa.nrao.edu/docs/)
- **CARTA help**: [CARTA manual](https://cartavis.org/)
- **CANFAR-specific issues**: [Slack channel](https://cadc.slack.com/archives/C01K60U5Q87)

### Common Issues
- **Memory errors**: Try using fewer cores or smaller image chunks
- **Slow performance**: Check if data is in `/arc/projects` (faster access)
- **CASA crashes**: See [container notes](../general/ALMA_Desktop/casa-containers.md) for known issues

### Community
Join the CANFAR Slack for:
- Sharing analysis tips
- Getting help with workflows
- Collaborating on techniques
- Discussing new features
