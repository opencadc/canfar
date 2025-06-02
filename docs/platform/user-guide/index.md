# User Guide

*Comprehensive documentation for the CANFAR Science Platform*

This guide provides detailed information for astronomers, grad students, and project managers using CANFAR for research. Whether you're analyzing radio astronomy data, building custom software environments, or managing large collaborative projects, this guide has you covered.

## What is CANFAR?

CANFAR provides **cloud-based astronomy computing** with:

- 🖥️ **Interactive sessions** (Jupyter Lab, CARTA, Firefly, Desktop environments)
- 💾 **Shared storage** for collaborative datasets (ARC, VOSpace, scratch)
- 🐳 **Pre-built software containers** with astronomy tools
- 🔧 **Custom container support** for specialized workflows
- ⚡ **Batch processing** for automated analysis
- 👥 **Collaboration tools** with group-based permissions

## 📖 Guide Structure

### [🧠 Concepts](concepts/index.md)

Understand the fundamentals: platform architecture, containers, Kubernetes, REST services, and VOSpace.

### [👥 Accounts & Permissions](accounts-permissions/index.md)

Manage users, groups, Harbor permissions, ACLs, and API access.

### [💾 Storage](storage/index.md)

Master ARC, VOSpace, and scratch storage systems. Learn data transfers, SSHFS, and the full VOSpace API.

### [🐳 Containers](containers/index.md)

Work with astronomy software containers, build custom environments, and publish to CANFAR.

### [🖥️ Interactive Sessions](interactive-sessions/index.md)

Launch Jupyter notebooks, CARTA, Firefly, desktop environments, and contributed applications.

### [⚡ Batch Jobs](batch-jobs/index.md)

Run headless containers, understand batch systems, manage logs, and use APIs for automation.

### [📡 Radio Astronomy](radio-astronomy/index.md)

Specialized workflows for CASA, ALMA data reduction, CARTA visualization, and other radio astronomy tools.

---

## 🎯 Choose Your Path

### 🌱 New Users

**First time using CANFAR?**

Start with our [Getting Started Guide](../get-started/index.md) for a structured learning path, then:

1. [Concepts](concepts/index.md) - Understand the platform
2. [Storage](storage/index.md) - Manage your data
3. [Interactive Sessions](interactive-sessions/index.md) - Start analyzing

### 🔬 Scientists & Researchers

**Ready to analyze data? Jump to your workflow:**

- **[🔭 Radio Astronomy](radio-astronomy/index.md)** - CASA, CARTA workflows and interferometry
- **[📊 Interactive Analysis](interactive-sessions/index.md)** - Jupyter notebooks, Python analysis
- **[🖥️ Desktop Applications](interactive-sessions/launch-desktop.md)** - GUI tools, CASA, DS9
- **[📁 Data Management](storage/index.md)** - Advanced transfer and organization

### ⚡ Advanced Users

**Looking for development and automation?**

- **[🐳 Container Usage](containers/index.md)** - Work with and build custom containers
- **[⚙️ Batch Processing](batch-jobs/index.md)** - Automated workflows and APIs
- **[🔐 Access Control](accounts-permissions/index.md)** - Groups and permissions management

---

## 🔗 Quick References

### Platform Access

- **[CANFAR Portal](https://www.canfar.net)** - Main interface
- **[File Manager](https://www.canfar.net/storage/arc/list)** - Browse storage
- **[Group Management](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/)** - Manage permissions

### APIs & Tools

- **[REST API Docs](https://ws-uv.canfar.net/)** - Programmatic access
- **[VOSpace Tools](storage/vospace-api.md)** - Advanced data management
- **[Harbor Registry](https://images.canfar.net/)** - Container repository

### Support

- **[💬 Discord Community](https://discord.gg/vcCQ8QBvBa)** - Community support
- **[📧 Email](mailto:support@canfar.net)** - Technical support
- **[FAQ](../faq/index.md)** - Common solutions

---

!!! info "Documentation Structure"
    This user guide is organized by workflow rather than by interface. Each section builds on previous concepts, so we recommend reading the Concepts section first if you're new to CANFAR.

---

## Citation

If you use CANFAR Science Platform for your research, please acknowledge CANFAR in publications:

!!! quote "Citation"
    The authors acknowledge the use of the Canadian Advanced Network for Astronomy Research (CANFAR) Science Platform. Our work used the facilities of the Canadian Astronomy Data Center, operated by the National Research Council of Canada with the support of the Canadian Space Agency, and CANFAR, a consortium that serves the data-intensive storage, access, and processing needs of university groups and centers engaged in astronomy research [(Fabbro et al. 2024)](https://doi.org/10.1117/12.3020588).

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="100" }
