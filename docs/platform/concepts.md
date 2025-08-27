# CANFAR Platform Concepts

Understanding the architecture and core concepts behind the CANFAR Science Platform.


!!! info "Quick Links"
    - [Get Started Guide](get-started.md)
    - [FAQ](../faq.md)
    - [Containers](containers.md)
    - [Interactive Sessions](guides/interactive-sessions/index.md)
    - [Batch Jobs](batch-jobs.md)
    - [Storage Guide](guides/storage/index.md)
    - [CANFAR Python Client](../client/home.md)
    - [Contact Support](help.md#contact-information-summary)

!!! abstract "🎯 What you'll learn"
    By the end of this guide, you'll understand:
    
    - How CANFAR's cloud architecture works
    - The role of containers in your research workflow
    - How sessions and storage systems interact
    - When to use different platform features


## 🚀 What is CANFAR?

The **Canadian Advanced Network for Astronomy Research (CANFAR)** Science Platform is a cloud-based computing environment designed specifically for astronomical research. For onboarding, see the [Getting Started Guide](get-started.md).

It provides:

- **On-demand computing resources** without needing your own servers
- **Pre-built software environments** with astronomy packages ready to use
- **Shared storage systems** for collaborative research
- **Scalable infrastructure** that grows with your project needs


!!! success "Key Benefit"
    CANFAR eliminates the traditional barriers of software installation, hardware management, and infrastructure setup, letting you focus entirely on your research.

!!! tip "Advanced: Platform Automation"
    - Use [CANFAR CLI](../cli/cli-help.md) and [Python Client](../client/home.md) for scripting and automation.
    - Integrate CANFAR with [GitHub Actions](https://github.com/features/actions) for automated workflows.


### Who Benefits from CANFAR?


See [Accounts & Permissions](accounts.md) for details on user roles and collaboration. For team onboarding, see [Get Started Guide](get-started.md).

=== "Individual Researchers"
    - **No software installation headaches** – pre-configured containers ready to use
    - Access powerful computing resources without owning hardware
    - Work from anywhere with just a web browser
    - Automatic backups and data protection

=== "Research Teams"
    - Share data and analysis environments seamlessly
    - Standardized software stacks across the team
    - Collaborative workspaces and session sharing
    - Centralized project management

=== "Large Projects"
    - Scale computing resources up or down as needed
    - Batch processing for large datasets
    - Custom software environments for specialized workflows
    - Integration with astronomy data archives

## 🏗️ Architecture

CANFAR is built on modern cloud-native technologies designed for scalability and reliability. Here's how the components work together:

```mermaid
%%{init: {'flowchart': {'curve': 'linear'}}}%%
graph LR
    %% User Entry Point
    User["👤 You"]:::user
    
    %% Portal Layer
    Portal["🌐 Science Portal<br/>canfar.net"]:::portal
    Auth["🔐 CADC Authentication"]:::auth
    Sessions["🖥️ Session Manager<br/>Skaha"]:::sessions
    
    %% Infrastructure Layer
    K8s["☸️ Kubernetes Cluster"]:::k8s
    Containers["🐳 Container Images<br/>Harbor Registry"]:::containers
    Storage["💾 Storage Systems"]:::storage
    
    %% Storage Systems
    arc["📁 arc POSIX Storage<br/>Shared Filesystem"]:::arc
    VOSpace["☁️ VOSpace Object Store<br/>Long-term Storage"]:::vospace
    Scratch["⚡ Scratch<br/>Temporary SSDs"]:::scratch
    
    %% Session Types
    Types["Session Types"]:::types
    Notebook["📓 Jupyter Notebooks"]:::notebooks
    Desktop["🖥️ Desktop Environment"]:::desktop
    CARTA["📊 CARTA Viewer"]:::carta
    Firefly["🔥 Firefly Viewer"]:::firefly
    Contrib["⚙️ Contributed Apps"]:::contrib
    Batch["🏭 Batch Jobs"]:::batch
    
    %% Connections
    User --> Portal
    Portal --> Auth
    Portal --> Sessions
    
    Auth --> K8s
    Sessions --> K8s
    
    K8s --> Containers
    K8s --> Storage
    
    Storage --> arc
    Storage --> VOSpace
    Storage --> Scratch
    
    Sessions --> Types
    Types --> Notebook
    Types --> Desktop
    Types --> CARTA
    Types --> Firefly
    Types --> Contrib
    Types --> Batch
    
    %% Styling
    classDef user fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000
    classDef portal fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef auth fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#000
    classDef sessions fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef k8s fill:#fff3e0,stroke:#ef6c00,stroke-width:3px,color:#000
    classDef containers fill:#f1f8e9,stroke:#558b2f,stroke-width:2px,color:#000
    classDef storage fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#000
    classDef arc fill:#fce4ec,stroke:#ad1457,stroke-width:2px,color:#000
    classDef vospace fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px,color:#000
    classDef scratch fill:#fff8e1,stroke:#f57f17,stroke-width:2px,color:#000
    classDef types fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#000
    classDef notebooks fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef desktop fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    classDef carta fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000
    classDef firefly fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000
    classDef contrib fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#000
    classDef batch fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#000
```

!!! info "Architecture Key Points"
    - **Science Portal**: Your web interface - no software installation required
    - **Kubernetes**: Manages your computing requirements automatically
    - **Containers**: Pre-built software environments with astronomy tools
    - **Storage Systems**: Multiple types optimized for different use cases
    - **Authentication**: Secure access via CADC integration


## 🐳 Containers


See [Container Usage](containers.md) for practical details and workflows. For building your own containers, see [Container Building](containers.md#building-custom-containers).

Containers are at the heart of CANFAR's flexibility and power. Think of them as complete, portable software environments that include everything needed to run specific applications.

!!! warning "Important Distinction"
    Unlike virtual machines that include entire operating systems, containers share the host's kernel and only package the application and its dependencies. This makes them faster, more efficient, and easier to distribute.

### Why Containers Matter for Astronomy

#### Traditional software installation

- Struggle with dependencies and conflicting versions
- Missing libraries and system requirements
- Different behaviour across different machines
- Time-consuming setup and configuration

#### CANFAR containers

- Consistent environment that works the same everywhere
- Pre-configured with astronomy packages
- No installation headaches
- Easy to share and reproduce results

!!! success "Research Reproducibility"
    Containers ensure your analysis runs the same way for you, your collaborators, and future researchers. This is crucial for reproducible science.


### Popular CANFAR Containers

See [Container Usage](containers.md) for a full list and details.

| Container | Purpose | Best For |
|-----------|---------|----------|
| **astroml** | General astronomy analysis | Python, NumPy, SciPy, Astropy, Matplotlib |
| **casa** | Radio interferometry | CASA software, Python, astronomy tools |
| **desktop** | GUI applications | Full Ubuntu desktop, Firefox, terminal |
| **carta** | Radio astronomy visualisation | CARTA viewer, analysis tools |
| **notebook** | Interactive computing | JupyterLab, Python scientific stack |


!!! tip "Getting Started"
    Start with the **astroml** container for general astronomy work. It includes most common packages and is regularly updated.

!!! tip "Advanced: Custom Containers"
    - Build your own containers for specialized workflows. See [Container Building](containers.md#building-custom-containers).
    - Use [Harbor Registry](https://images.canfar.net/) to browse and manage images.

### Container Lifecycle

When you launch a session, here's what happens behind the scenes:

1. **Request**: You choose a container type in the Science Portal
2. **Download**: Kubernetes pulls the container image (first time: 2-3 minutes)
3. **Launch**: Container starts with your storage connected
4. **Work**: You use the pre-configured environment
5. **Cleanup**: Container is destroyed when session ends (files persist in storage)

!!! info "Performance Note"
    Subsequent launches of the same container are much faster (30-60 seconds) since the image is cached locally.


## ☸️ Sessions and Computing Resources


See [Interactive Sessions](guides/interactive-sessions/index.md) for session workflows and examples. For batch processing, see [Batch Jobs](batch-jobs.md).

CANFAR uses Kubernetes to manage your computing sessions. You don't need to understand Kubernetes deeply, but here are the key concepts:


!!! abstract "Session Fundamentals"
    - **Temporary**: Each session creates a new container instance
    - **Persistent Data**: Files persist through storage systems, not containers
    - **Resource Limits**: CPU, memory, and storage based on your request

!!! tip "Advanced: Session Management"
    - Use `canfar info [session-id]` and `canfar stats` to monitor and debug sessions.
    - For automation, see [Python Client](../client/home.md).

### Session Types

Different session types provide different interfaces to the same underlying computing resources:

=== "📓 Notebook Sessions"
    **JupyterLab Interface** for interactive analysis

    - Perfect for data exploration and visualization
    - Python, R, and other kernels available
    - Rich text, code, and visualization in one interface

=== "🖥️ Desktop Sessions"
    **Full Linux desktop environment** for GUI applications

    - CASA, DS9, and image viewers
    - Traditional desktop workflow
    - Multiple applications running simultaneously

=== "📊 CARTA Sessions"
    **Specialized for radio astronomy** visualization and analysis

    - CARTA viewer for FITS files
    - Radio astronomy workflows
    - Interactive data exploration

=== "🔥 Firefly Sessions"
    **Table and image visualization** tools

    - Astronomical table viewing
    - Image display and analysis
    - Web-based interface

=== "⚙️ Contributed Sessions"
    **Custom applications** contributed by the community
    
    - Specialized tools and workflows
    - Community-maintained software
    - Experimental features

### Session Resource Allocation

CANFAR supports two resource allocation modes that determine how CPU and memory are allocated to your sessions:

!!! info "Flexible Sessions (Default)"
    **Adaptive resource allocation** that adjusts to your needs:

    - **:material-trending-up: Dynamic Usage**: Sessions can use more CPU and memory when cluster resources are available
    - **:material-rocket-launch: Fast Scheduling**: Sessions start quickly as they're easier to place on available nodes
    - **:material-chart-line-variant: Variable Performance**: Performance adapts to cluster load and other users' activity
    - **:material-kubernetes: Kubernetes QoS**: Runs as "Burstable" quality of service class

!!! warning "Fixed Sessions"
    **Guaranteed resource allocation** with dedicated resources:

    - **:material-speedometer: Predictable Performance**: Consistent CPU and memory allocation regardless of cluster load
    - **:material-lock: Resource Reservation**: Resources are reserved exclusively for your session
    - **:material-clock-alert: Scheduling Delays**: May take longer to start if exact resources aren't immediately available
    - **:material-kubernetes: Kubernetes QoS**: Runs as "Guaranteed" quality of service class

#### When to Choose Each Mode

=== "🔄 Flexible Mode (Default)"

    !!! info ""
        **Best for most research workflows:**

        - Interactive data exploration and analysis
        - Development and testing of code
        - Learning and experimentation
        - Workflows with variable resource needs
        - General-purpose computing tasks

        **Example Use Cases:**

        - Jupyter notebook sessions for data analysis
        - Testing new analysis pipelines
        - Interactive visualization with CARTA or Firefly
        - Educational workshops and tutorials

        **Example Commands:**

        ```bash
        canfar create notebook skaha/base-notebook:latest
        canfar create headless skaha/base-notebook:latest -- python script.py
        ```

=== "🎯 Fixed Mode"

    !!! warning ""
        **Best for production and critical workloads:**

        - Production data processing pipelines
        - Time-sensitive computations
        - Large-scale batch processing with known requirements
        - Performance benchmarking
        - Critical deadlines requiring consistent performance

        **Example Use Cases:**

        - Processing large survey datasets
        - Running computationally intensive simulations
        - Batch processing with strict time constraints
        - Performance-critical analysis workflows

        **Example Commands:**

        ```bash
        canfar create notebook skaha/base-notebook:latest --cpu 4 --memory 8
        canfar create headless skaha/base-notebook:latest --cpu 2 --memory 4 -- python script.py
        ```

#### Resource Allocation in Practice

| Aspect | Flexible Mode | Fixed Mode |
|--------|---------------|------------|
| **Resources** | Optional (defaults to flexible) | Required (explicit values) |
| **Startup Time** | Faster | Variable (may wait for resources) |
| **Performance** | Variable, can burst higher | Consistent, predictable |
| **Efficiency** | High (shared resources) | Lower (dedicated resources) |
| **Best Use Case** | Interactive, exploratory work | Production, critical workloads |

!!! tip "Getting Started"
    Start with **flexible mode** (the default) for most work. Only switch to **fixed mode** when you need guaranteed performance or have specific resource requirements.

## 💾 Storage Systems


See the [Storage Guide](guides/storage/index.md) for practical usage and quotas. For VOSpace scripting, see [VOSpace API](guides/storage/vospace-api.md).

### Data Persistence Rules

CANFAR provides multiple storage systems optimised for different use cases:

!!! warning "Critical: Where Your Files Are Saved"
    Understanding where your files persist is crucial for not losing work:

| Location | Persistence | Best For |
|----------|-------------|----------|
| `/arc/projects/[project]/` | ✅ **Permanent, backed up** | Datasets, results, shared code |
| `/arc/home/[user]/` | ✅ **Permanent, backed up** | Personal configs, small files |
| `/scratch/` | ❌ **Wiped at session end** | Large computations, temporary files |
| `/tmp/` | ❌ **Lost when session ends** | Temporary processing only |

### ARC Storage (`/arc/`)

**High-performance POSIX file system** for active research:

- **Speed**: Fast, direct access for large computations
- **Sharing**: Group-based access control
- **Backup**: Daily snapshots
- **Best For**: Active analysis, large datasets, collaborative work

### VOSpace (`vos:`)


**Web-accessible object store** for long-term storage:

- **IVOA**: Based on the International Virtual Observatory Alliance (IVOA) standard
- **Access**: Web APIs and command-line tools
- **Metadata**: Astronomical metadata support
- **Versioning**: Track changes to datasets
- **Best For**: Archives, sharing, backups, metadata-rich data



!!! tip "Storage Strategy"
    Use **ARC storage** for active analysis and **VOSpace** for long-term archival and sharing.

!!! tip "Advanced: Data Automation"
    - Automate data transfers with [CANFAR Python Client](../client/home.md) and [VOSpace API](guides/storage/vospace-api.md).
    - Use [Git LFS](https://git-lfs.github.com/) for versioning large datasets.

### Storage Comparison

| Feature | ARC Storage (`/arc/`) | VOSpace (`vos:`) |
|---------|----------------------|------------------|
| **Access Method** | POSIX file system | Web APIs, command tools |
| **Speed** | Fast (direct access) | Medium (network-based) |
| **Best For** | Active analysis, large computations | Archives, sharing, backups |
| **Quota** | Group-based | User/project based |
| **Backup** | Daily snapshots | Geo-redundant |


## 🌐 Programmatic Access

See [CANFAR Python Client](../client/home.md) and [VOSpace API](guides/storage/vospace-api.md) for automation and scripting.

CANFAR provides REST APIs for programmatic access, allowing you to:

- Launch and manage sessions from scripts
- Transfer files programmatically
- Integrate CANFAR into automated workflows
- Build custom applications using CANFAR resources

### Key API Endpoints

| Service | Purpose | Documentation |
|---------|---------|---------------|
| **CANFAR Python Client** | Session management | [`canfar`](../client/home.md) |
| **VOSpace** | File operations | [VOSpace API](guides/storage/vospace-api.md) |
| **Access Control** | Authentication and Authorization | [CADC Services](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/ac) |


!!! info "Advanced Users"
    The REST APIs enable automation and integration with external tools and workflows.
    For example workflows, see [Client Examples](../client/examples.md).

## 🔗 What's Next?

Now that you understand the core concepts, dive into specific areas:

- **[Accounts & Permissions →](accounts.md)** - Manage users and access
- **[Storage Systems →](guides/storage/index.md)** - Master data management
- **[Container Usage →](containers.md)** - Work with software environments
- **[Interactive Sessions →](guides/interactive-sessions/index.md)** - Start analyzing data

---

!!! success "Key Takeaway"
    CANFAR provides the computing power of a research institution without the infrastructure overhead. Focus on your science - let CANFAR handle the computers, software, and data management.
