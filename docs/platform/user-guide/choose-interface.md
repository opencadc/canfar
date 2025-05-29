# Choose Your Interface

CANFAR offers several interfaces for different types of work. Choose the one that best fits your needs:

## 📓 Jupyter Notebooks

**Best for**: Data analysis, Python/R programming, exploratory research

### Jupyter Features

- JupyterLab interface with notebooks, terminal, and file browser
- Pre-installed astronomy libraries (astropy, numpy, matplotlib, etc.)
- Easy data visualization and sharing
- Support for Python, R, and Julia kernels

### Ideal for Researchers Who

- Want to analyze data interactively
- Need to create reproducible analysis workflows  
- Prefer coding in Python or R
- Want to share results with collaborators

[**🚀 Launch Notebook Tutorial**](launch-notebook.md){ .md-button .md-button--primary }

---

## 🔭 CARTA (Radio Astronomy)

**Best for**: FITS/HDF5 image viewing, radio astronomy data analysis

!!! info "CANFAR Team Supported"
    CARTA is officially supported by the CANFAR team, providing reliable performance and regular updates.

### CARTA Features

- **Browser-based astronomy image viewer** optimized for large datasets
- **Advanced visualization tools** specifically designed for radio data
- **Support for large datasets and data cubes** with efficient streaming
- **Interactive measurement and annotation tools** for detailed analysis
- **Multi-file comparison** and blinking capabilities
- **Spectral profile extraction** from data cubes
- **Region analysis** with statistics and export functionality

### Best Suited For

- Work with radio astronomy data (VLA, ALMA, JVLA, etc.)
- Need to inspect FITS or HDF5 files efficiently
- Want advanced image analysis capabilities
- Analyze data cubes from interferometers
- Need to visualize large (multi-GB) astronomical images
- Require professional-grade astronomical visualization

[**🚀 Launch CARTA Tutorial**](launch-carta.md){ .md-button .md-button--primary }

---

## 🖥️ Desktop Environment  

**Best for**: Full Linux desktop, CASA, DS9, traditional astronomy software

!!! info "CANFAR Team Supported"
    Desktop Sessions are officially supported by the CANFAR team. This is different from community-contributed desktop-app containers.

### Desktop Environment Features

- **Complete Linux desktop** accessible through your browser
- **Pre-installed astronomy software** (CASA, DS9, TOPCAT, etc.)
- **Full command-line environment** with standard Linux tools
- **Firefly astronomical image viewer** for advanced FITS visualization
- **Web-based desktop interface** with window management
- **File manager integration** with ARC storage
- **Multi-application support** running simultaneously

### Key Applications Available

- **CASA**: Radio interferometry data reduction (all versions)
- **DS9**: FITS image display and analysis
- **TOPCAT**: Interactive catalog analysis and visualization
- **Firefly**: Web-based astronomical image viewer with advanced features
- **Standard Linux tools**: editors, terminals, file managers

### Desktop Sessions vs Desktop Apps

- **Desktop Sessions** (this interface): Full desktop environment, CANFAR team supported
- **Desktop Apps** (custom containers): Individual applications, community contributed

### Optimal for Users Who

- Need CASA for interferometry data reduction
- Want a familiar desktop environment with multiple applications
- Need to run GUI-based astronomy tools
- Prefer traditional desktop workflows
- Want access to Firefly's advanced FITS visualization

[**🚀 Launch Desktop Tutorial**](launch-desktop.md){ .md-button .md-button--primary }

---

## 🔧 Custom Applications

**Best for**: Specialized software, custom workflows

!!! warning "Community Contributed"
    Custom applications are contributed by the community. While useful, they may have different support levels than CANFAR team supported interfaces.

### Custom Application Features

- **VSCode server** for web-based development
- **Pluto notebooks** for interactive Julia programming
- **Custom containers** built by research collaborations
- **Specialized analysis tools** for specific research domains
- **Desktop-app containers** for individual applications

### Container Types

- **Notebook containers**: Specialized Jupyter environments
- **Desktop-app containers**: Individual GUI applications
- **Headless containers**: Background processing and automation
- **Contributed containers**: Community-developed tools

### Great Choice For Users Who

- Need specific software not available in other interfaces
- Want to use VSCode in the browser
- Have custom containers for your research
- Need specialized development environments
- Want to try community-contributed tools

[**📖 Learn About Custom Containers**](../developer-guide/containers.md){ .md-button }

---

## Quick Comparison

| Interface | Learning Curve | Best For | Launch Time | Support Level |
|-----------|----------------|----------|-------------|---------------|
| **Notebooks** | ⭐⭐ Easy | Data analysis, Python | ~30 seconds | CANFAR Team |
| **CARTA** | ⭐⭐ Easy | Image viewing, radio data | ~30 seconds | CANFAR Team |
| **Desktop** | ⭐⭐⭐ Moderate | CASA, GUI tools, Firefly | ~60 seconds | CANFAR Team |
| **Custom** | ⭐⭐⭐⭐ Advanced | Specialized workflows | ~60 seconds | Community |

## CANFAR Team Supported vs Community Contributed

### 🏆 CANFAR Team Supported (Recommended for most users)

- **Desktop Sessions**: Full Linux desktop with astronomy software
- **CARTA**: Professional radio astronomy image viewer  
- **Jupyter Notebooks**: Data analysis and programming environment

**Benefits**: Regular updates, official support, guaranteed compatibility, performance optimization

### 👥 Community Contributed

- **Desktop-app containers**: Individual applications in containers
- **Custom analysis tools**: Specialized research software
- **Experimental interfaces**: Cutting-edge tools and workflows

**Benefits**: Access to specialized tools, community innovation, diverse software options

---

## What's Next?

After choosing your interface, learn about the storage system:

[**→ Understanding Storage**](../storage-systems-guide.md){ .md-button }

---

## Still Not Sure?

### For Radio Astronomers

Start with **Desktop** to access CASA and Firefly, then try **CARTA** for advanced data visualization.

### For Optical/IR Astronomers  

Start with **Notebooks** for data analysis, then explore **Desktop** for DS9, Firefly, and other tools.

### For Data Scientists

**Notebooks** will feel most familiar and provide the best Python data science environment.

### For Software Developers

Try **Custom Applications** with VSCode server for web-based development.

### Need Help Deciding?

Ask in our [Slack channel](https://cadc.slack.com/archives/C01K60U5Q87) - the community is very helpful!
