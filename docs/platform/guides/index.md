# User Guides

This guides provides detailed information for astronomers, grad students, and project managers using CANFAR for research. Whether you're analyzing radio astronomy data, building custom software environments, or managing large collaborative projects, this guide has you covered.

## 📖 Guide Structure

### [🧠 Concepts](../concepts.md)

Understand the fundamentals: platform architecture, containers, Kubernetes, REST services, and VOSpace.

### [👥 Accounts & Permissions](../accounts.md)

Manage users, groups, Harbor permissions, ACLs, and API access.

### [💾 Storage](storage/index.md)

Master `/arc`, VOSpace `vault`, and scratch storage systems. Learn data transfers, `sshfs`, and the full VOSpace API.

### [🐳 Containers](../containers.md)

Work with astronomy software containers, build custom environments, and upload to CANFAR Science Platform.

### [🖥️ Interactive Sessions](interactive-sessions/index.md)

Launch Jupyter notebooks, CARTA, Firefly, desktop environments, and contributed applications.

### [⚡ Batch Jobs](../batch-jobs.md)

Run "headless" containers, understand batch systems, manage logs, and use APIs for automation.

### [📡 Radio Astronomy](radio-astronomy/index.md)

Specialized workflows for CASA, ALMA data reduction, CARTA visualization, and other radio astronomy tools.

### [🗂️ Legacy Documentation]()

In addition to the core modules (Accounts, Storage, Containers, Interactive Sessions, etc.), a set of legacy documents is also available. These cover earlier CANFAR service portals and workflows - [Cloud Services](../legacy/cloud-services.md), which historically paralleled features such as Group Management, Science Portal, and CADC Search.  

---

## 🎯 Choose Your Path

### 🌱 New Users

**First time using CANFAR?**

Start with our [Getting Started Guide](../get-started.md) for a structured learning path, then:

1. [Concepts](../concepts.md) - Understand the platform
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

- **[🐳 Container Usage](../containers.md)** - Work with and build custom containers
- **[⚙️ Batch Processing](../batch-jobs.md)** - Automated workflows and APIs
- **[🔐 Access Control](../accounts.md)** - Groups and permissions management

---

## 🔗 Quick References

### Platform Access

- **[CANFAR Portal](https://www.canfar.net/science-portal/)** - Main interface
- **[File Manager](https://www.canfar.net/storage/arc/list)** - Browse storage on `/arc` and `vault`
- **[Group Management](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/)** - Manage teams and their permissions

### APIs & Tools

- **[REST API Docs](https://ws-uv.canfar.net/skaha)** - Programmatic access for `skaha`
- **[VOSpace Tools](storage/vospace-api.md)** - Advanced data management
- **[Container Registry](https://images.canfar.net/)** - Container registry for teams (Harbor)

### Quick Commands Reference

#### Storage Commands
```bash
# Check storage usage
df -h /arc/projects/myproject
du -sh /arc/home/$USER

# VOSpace operations
vls vos:myproject              # List files
vcp file.fits vos:myproject/   # Upload
vcp vos:myproject/file.fits .  # Download
```

#### Session Management (CLI)
```bash
# Get authentication token
canfar auth login

# Launch notebook session
canfar create notebook --name analysis --cores 2 --ram 8 images.canfar.net/skaha/astroml:latest

# List active sessions
canfar ps
```

#### Container Operations
```bash
# Login to container registry
docker login images.canfar.net

# Build and push custom container
docker build -t images.canfar.net/myproject/tool:latest .
docker push images.canfar.net/myproject/tool:latest

# Run container locally for testing
docker run -it --rm \
  -v /path/to/data:/arc/projects/test \
  images.canfar.net/skaha/astroml:latest /bin/bash
```

### Support

- **[💬 Discord Community](https://discord.gg/vcCQ8QBvBa)** - Community support
- **[FAQ](../../faq.md)** - Common solutions
- **[Email Support](mailto:support@canfar.net)** - Direct assistance

---

!!! info "Documentation Structure"
    This user guide is organized by workflow rather than by interface. Each section builds on previous concepts, so we recommend reading the Concepts section first if you're new to CANFAR.

---

## Citation

If you use CANFAR Science Platform for your research, please acknowledge CANFAR in publications:

!!! quote "Citation"
    The authors acknowledge the use of the Canadian Advanced Network for Astronomy Research (CANFAR) Science Platform. Our work used the facilities of the Canadian Astronomy Data Center, operated by the National Research Council of Canada with the support of the Canadian Space Agency, and CANFAR, a consortium that serves the data-intensive storage, access, and processing needs of university groups and centers engaged in astronomy research. 
    
If you need to refer to a paper, you can use this  [(SPIE 2024 citation)](https://doi.org/10.1117/12.3020588).

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="100" }