# 📦 Available Containers

Comprehensive reference for pre-built containers available on the CANFAR Science Platform.

## 🔍 Container Overview

CANFAR provides pre-built containers with scientific software stacks optimized for astronomy and data science. All containers are maintained by CANFAR and regularly updated with the latest software versions.

**Container Registry**: [images.canfar.net](https://images.canfar.net)  
**Source Code**: [science-containers.git](https://github.com/opencadc/science-containers.git)

---

## 🏗️ Container Architecture

CANFAR containers follow a hierarchical build structure to ensure consistency and efficiency:

```text
Ubuntu LTS (Base Operating System)
│
├── base (headless)
│   │   • Core development tools
│   │   • System libraries
│   │   • Conda package manager
│   │
│   └── astroml (headless)
│       │   • Astronomy libraries (astropy, astroquery)
│       │   • Machine learning (scikit-learn, tensorflow)
│       │   • Data science (pandas, matplotlib, jupyter)
│       │
│       ├── astroml-notebook (for Jupyter sessions)
│       ├── astroml-vscode (for VSCode development)
│       └── astroml-desktop (for desktop applications)
│
└── Desktop Applications (legacy software)
    • CASA, Topcat, Aladin
    • Specialized astronomy tools
    • May use different base systems
```

---

## 📋 Container Types by Use Case

### 🐍 Data Science & Analysis

| Container | Use Case | Key Software | Session Type |
|-----------|----------|-------------|--------------|
| **astroml-notebook** | Interactive data analysis | Jupyter Lab, astropy, pandas, matplotlib | Notebook |
| **astroml** | Command-line processing | Python libraries, no GUI | Headless |
| **astroml-vscode** | Code development | VSCode, Python tools, extensions | Contributed |

### 🖥️ Desktop Applications

| Container | Use Case | Key Software | Session Type |
|-----------|----------|-------------|--------------|
| **astroml-desktop** | General desktop + astronomy | Full desktop + astroml libraries | Desktop |
| **casa** | Radio astronomy analysis | CASA software suite | Desktop |
| **carta** | Image visualization | CARTA viewer | Contributed |

### ⚡ GPU-Accelerated

All standard containers have GPU-enabled versions with NVIDIA CUDA support:

- **astroml-gpu**: CUDA-enabled data science
- **astroml-gpu-notebook**: GPU Jupyter environment
- **astroml-gpu-desktop**: GPU desktop environment

---

## 🔧 Software Included

### Core Astronomy Libraries
- **Astropy**: Core astronomy functionality
- **Astroquery**: Query astronomical databases
- **Photutils**: Photometry and aperture analysis
- **Specutils**: Spectroscopy tools
- **Reproject**: Image reprojection utilities

### Data Science Stack
- **NumPy/SciPy**: Numerical computing
- **Pandas**: Data manipulation and analysis
- **Matplotlib/Seaborn**: Data visualization
- **Scikit-learn**: Machine learning
- **TensorFlow/PyTorch**: Deep learning (GPU versions)

### Development Tools
- **Jupyter Lab**: Interactive notebooks
- **VSCode**: Integrated development environment
- **Git**: Version control
- **Conda**: Package management

---

## 🚀 Getting Started

### Choose Your Container

1. **For Jupyter notebooks**: `astroml-notebook`
2. **For desktop applications**: `astroml-desktop` 
3. **For code development**: `astroml-vscode`
4. **For batch processing**: `astroml` (headless)
5. **For GPU computing**: Any `*-gpu` variant

### Launch Instructions

Visit the [CANFAR Portal](https://www.canfar.net) and:

1. Click **"Launch"** → Choose your session type
2. Select your preferred container from the dropdown
3. Configure resources (CPU, RAM, GPU if needed)
4. Click **"Launch Session"**

**Detailed Guides**:
- [Notebook Sessions](../user-guide/launch-notebook.md)
- [Desktop Sessions](../user-guide/launch-desktop.md) 
- [CARTA Sessions](../user-guide/launch-carta.md)

---

## 🔧 Building Custom Containers

Need specialized software not included in standard containers?

**→ [Container Building Guide](../container-building-guide.md)**

Learn how to:
- Create containers based on CANFAR standards
- Add custom software and dependencies
- Test and publish to the CANFAR registry
- Share containers with your research team

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="200" }
