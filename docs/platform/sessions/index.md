# Interactive Sessions

**CANFAR computing environments for astronomical research - Jupyter notebooks, and non-interactive applications.**

!!! abstract "🎯 Session Types Overview"
    **Choose the right interface for your research:**
    
    - **[Jupyter Notebooks](notebook.md)**: Interactive data analysis and visualisation
    - **[Desktop Environment](desktop.md)**: Full Linux desktop with GUI applications  
    - **[CARTA Viewer](carta.md)**: Radio astronomy visualisation and analysis
    - **[Firefly Viewer](firefly.md)**: Table and image viewing for surveys
    - **[Contributed Apps](contributed.md)**: Specialised community applications
    - **[Batch Processing](batch.md)**: Automated and large-scale workflows

## 🚀 Session Fundamentals

### What are Interactive Sessions?

Interactive sessions provide on-demand access to pre-configured computing environments running in containers. Each session type offers different interfaces optimised for specific astronomical workflows.

### Key Benefits

**No Installation Required**
:   Access complex astronomy software through your web browser without local installation or configuration.

**Pre-Configured Environments**
:   Containers include popular astronomy packages like AstroPy, CASA, and scientific Python libraries ready to use.

**Persistent Data Access**
:   All sessions automatically connect to your ARC storage and can access VOSpace for long-term data management.

**Scalable Resources**
:   Choose flexible or fixed resource allocation based on your computational requirements.

## 📊 Session Type Comparison

| Session Type | Interface | Best For | GUI Support |
|--------------|-----------|----------|-------------|
| **[Notebook](notebook.md)** | JupyterLab | Data analysis, prototyping, documentation | ✅ Web-based |
| **[Desktop](desktop.md)** | Full Linux desktop | CASA, image viewers, traditional software | ✅ Desktop GUI |
| **[CARTA](carta.md)** | CARTA interface | Radio astronomy visualisation | ✅ Specialised |
| **[Firefly](firefly.md)** | Firefly viewer | Catalogue analysis, image display |  ✅ Web-based |
| **[Contributed](contributed.md)** | Various | Specialised applications | ⚠️ Varies |
| **[Batch](batch.md)** | None (headless) | Large-scale processing | ❌ Headless |

## 🔧 Session Management

### Creating Sessions

**Via Science Portal:**
:   Launch sessions through the [CANFAR Science Portal](https://www.canfar.net/science-portal/) web interface with point-and-click simplicity.

**Via Command Line:**
:   Use the [CANFAR CLI](../../cli/cli-help.md) for scripted session creation and automation.

**Via Python API:**
:   Integrate session management into custom workflows using the [CANFAR Python Client](../../client/home.md).

### Session Lifecycle

**Creation** (30 seconds - 3 minutes)
:   Container download (first time) and startup with storage mounting

**Active Use**
:   Full access to computing resources and storage systems

**Idle Management**
:   Sessions automatically suspend after periods of inactivity to conserve resources

**Termination**
:   Container deletion with data preserved in persistent storage

!!! warning "Data Persistence"
    **Important**: Session containers are temporary. Always save important work to `/arc/` storage or VOSpace before ending sessions.

## 📈 Resource Allocation

### Flexible Allocation (Default)

**Advantages:**
- Faster session startup
- Can burst to higher resource usage when available
- Optimal for interactive work and development

**Best For:**
- Data exploration and analysis
- Development and testing
- Educational workshops

### Fixed Allocation

**Advantages:**
- Guaranteed consistent performance
- Predictable resource availability
- Better for production workloads

**Best For:**
- Large-scale processing
- Performance-critical analysis
- Time-sensitive computations

### Resource Selection Guide

| Workflow Type | Recommended Mode | CPU/Memory | Duration |
|---------------|------------------|------------|----------|
| **Interactive Analysis** | Flexible | 2-4 CPU, 4-8GB | Hours |
| **Large Dataset Processing** | Fixed | 4-8 CPU, 16-32GB | Hours-Days |
| **Development & Testing** | Flexible | 1-2 CPU, 2-4GB | Hours |
| **Production Pipelines** | Fixed | Varies by workload | Days |

## 🔗 Integration with Platform Services

### Storage Integration

All interactive sessions automatically mount:

- **ARC Home** (`/arc/home/[user]/`): Personal configurations and scripts
- **ARC Projects** (`/arc/projects/[project]/`): Shared research data and results
- **Scratch** (`/scratch/`): High-speed temporary storage for processing

Additional storage accessible via API:
- **VOSpace** (`vos:`): Long-term archives and data sharing

### Container Environments

Sessions run in [container environments](../containers/index.md) that include:

- Operating system (typically Ubuntu Linux)
- Astronomy software packages (AstroPy, CASA, etc.)
- Scientific computing libraries (NumPy, SciPy, Matplotlib)
- Development tools and utilities

### Authentication & Permissions

Sessions inherit your [CANFAR permissions](../permissions.md):

- Automatic access to your group projects
- Secure integration with CADC services
- API access for automated workflows

## 🎯 Choosing Your Session Type

### For Data Analysis

**New to CANFAR?** → Start with **[Jupyter Notebooks](notebook.md)**
:   Familiar interface combining code, documentation, and visualisation

**Need GUI Applications?** → Use **[Desktop Sessions](desktop.md)**
:   Full Linux desktop for CASA, image viewers, and traditional software

### For Astronomy Specialisations

**Radio Astronomy** → **[CARTA Viewer](carta.md)**
:   Optimised for radio interferometry data visualisation and analysis

**Survey Data** → **[Firefly Viewer](firefly.md)**
:   Efficient table and image viewing for large astronomical catalogues

**Specialised Tools** → **[Contributed Applications](contributed.md)**
:   Community-maintained applications for specific research domains

### For Production Work

**Large-Scale Processing** → **[Batch Sessions](batch.md)**
:   Automated workflows for processing large datasets without interactive interfaces

