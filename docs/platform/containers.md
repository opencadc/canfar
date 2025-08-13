# Containers

**Working with astronomy software containers on CANFAR**

!!! abstract "🎯 What You'll Learn"
    - What containers are and how they run on CANFAR
    - How container types map to session types (Notebook, Desktop, Headless)
    - How to choose and use existing containers effectively
    - How containers are categorized (CANFAR-supported, community, team)
    - How to build, manage, version, and distribute custom containers
    - How containers integrate with CANFAR storage and workflows

Containers provide pre-packaged software environments that include everything needed to run astronomy applications. On CANFAR, containers eliminate the "works on my machine" problem by ensuring consistent, reproducible computational environments across different sessions and workflows.

!!! success "Key Concept: Reproducible Environments"
    Containers provide consistent, reproducible software environments for astronomy work across sessions and teams.

## Understanding CANFAR Containers

Think of containers as complete software packages that bundle an operating system (typically Ubuntu Linux), astronomy software like CASA or Python packages, programming tools, system libraries, and environment configuration into a single portable unit. When you launch a session on CANFAR, you're essentially starting up one of these pre-configured environments with your data and home directory automatically mounted and accessible.

The container ecosystem on CANFAR follows a layered approach. Base containers provide fundamental tools and the conda package manager, while specialized containers build upon these foundations to offer domain-specific software stacks. This architecture ensures consistency while allowing flexibility for different research needs.

### Runtime Environment

!!! info "How Containers Run on CANFAR"
    - Containers run as your CADC user (not root)
    - `/arc/home/[username]` is the container's home directory
    - Project directories under `/arc/projects/` are mounted and accessible
    - `/scratch/` provides high-speed temporary storage

```bash
# Inside a running container, check your environment
echo $USER                      # Your CADC username
echo $HOME                      # /arc/home/[username]
ls /arc/projects/               # Available project directories
ls /scratch/                    # Temporary high-speed storage
```

This runtime setup means there's an important compatibility consideration between code packaged in the container image and code stored on the `/arc` filesystem. Best practice involves keeping stable, tested code within the container image while placing development scripts and analysis notebooks in your `/arc/home` or project directories where they can be easily modified and version controlled.

!!! warning "Persistence Reminder"
    Software installed inside a running container (e.g., `pip install --user`) is temporary and lost when the session ends. Keep stable software in the image; keep notebooks/scripts on `/arc`.

---

## Container Types and Session Integration

CANFAR containers are designed to work with different session types, each optimized for specific workflows and interaction patterns.

### Notebook Containers

Notebook containers provide interactive Jupyter environments accessed through your web browser. These containers must include Jupyter Lab and are optimized for data analysis, visualization, and interactive computing. The **astroml** container exemplifies this type, offering a comprehensive Python astronomy stack with popular packages like Astropy, SciPy, and scikit-learn.

```python
# Example notebook session - check available packages
import astropy
import numpy as np
import matplotlib.pyplot as plt
from astroquery import vizier

print(f"Astropy version: {astropy.__version__}")
print(f"NumPy version: {np.__version__}")

# Access your data
import os

data_path = f"/arc/projects/{os.environ.get('PROJECT_NAME', 'myproject')}"
print(f"Project data at: {data_path}")
```

For GPU-accelerated computing, **astroml-cuda** includes the CUDA toolkit alongside the standard astronomy libraries, enabling machine learning and image processing workflows that leverage GPU acceleration.

```python
# Check GPU availability in astroml-cuda container
import torch
import tensorflow as tf

print(f"PyTorch CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU device: {torch.cuda.get_device_name(0)}")

print(f"TensorFlow GPU devices: {len(tf.config.list_physical_devices('GPU'))}")
```

### Desktop-App Containers

While CANFAR maintains the base **desktop** container that provides the Ubuntu desktop environment, users can create **desktop-app** containers that package specific GUI applications to run within desktop sessions. These containers focus on single applications or related tool suites rather than providing complete desktop environments.

```dockerfile
# Example desktop-app container for DS9 image viewer
FROM ubuntu:22.04

# Install DS9 and dependencies
RUN apt-get update && apt-get install -y \
    saods9 \
    x11-apps \
    libx11-6 \
    libxft2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create startup script
RUN echo '#!/bin/bash\nds9 "$@"' > /usr/local/bin/start-ds9 && \
    chmod +x /usr/local/bin/start-ds9

# Default command for desktop session
CMD ["/usr/local/bin/start-ds9"]
```

Desktop-app containers are particularly useful for legacy astronomy software, specialized visualization tools, or applications that require specific library versions or configurations. When launched in a desktop session, these applications integrate seamlessly with the desktop environment while maintaining their isolated software dependencies.

### Headless Containers

Headless containers run without graphical interfaces and are designed for batch processing and automated workflows. These containers execute through the batch job system and are optimized for non-interactive processing tasks like data reduction pipelines, large-scale analysis, or scheduled computations.

```dockerfile
# Example headless processing container
FROM images.canfar.net/skaha/astroml:latest

# Install additional processing tools
USER root
RUN apt-get update && apt-get install -y \
    parallel \
    rsync \
    && apt-get clean

USER ${NB_USER}

# Copy processing scripts
COPY scripts/ /opt/processing/
RUN chmod +x /opt/processing/*.sh

# Default processing command
CMD ["/opt/processing/batch_process.sh"]
```

---

## Working with Existing Containers

Most astronomy work on CANFAR can be accomplished using existing containers without requiring custom builds. The **astroml** container covers the majority of Python-based astronomy analysis needs, while **casa** handles radio astronomy workflows. For GUI applications, the **desktop** container provides a complete environment with Firefox, file managers, and terminal access.

Choosing the right container depends on your specific workflow requirements. General Python astronomy work benefits from **astroml** in either notebook or desktop terminal sessions. Radio astronomy tasks requiring CASA tools work best with the **casa** container in notebook or desktop modes. Legacy GUI applications or IDL-based workflows should use **desktop** sessions with the desktop container.

```bash
# Launch different session types via API
TOKEN=$(curl -s https://ws-cadc.canfar.net/ac/login \
  -d "username=myuser" -d "password=mypass" | tr -d '"')

# Notebook session with astroml
curl -H "Authorization: Bearer $TOKEN" \
  -d "name=analysis-session" \
  -d "image=images.canfar.net/skaha/astroml:latest" \
  -d "type=notebook" \
  -d "cores=2" -d "ram=4" \
  https://ws-uv.canfar.net/skaha/v0/session

# Desktop session with CASA
curl -H "Authorization: Bearer $TOKEN" \
  -d "name=casa-desktop" \
  -d "image=images.canfar.net/skaha/casa:latest" \
  -d "type=desktop" \
  -d "cores=4" -d "ram=8" \
  https://ws-uv.canfar.net/skaha/v0/session
```

!!! tip "Best Practice: Code Placement"
    Keep stable, tested code inside the container image. Keep frequently edited analysis code and notebooks in `/arc/home` or project directories.

!!! warning "Temporary Installs"
    Software installations using `pip install --user` or `apt` inside a running container are temporary and will be lost when the session ends.

---

## Container Categories

CANFAR containers fall into three main categories, each serving different purposes and maintained by different groups.

### CANFAR-Supported Containers

These are officially maintained by the CANFAR team and provide the foundation for most astronomy work. The core offerings include **astroml** for general astronomy analysis with Python, Astropy, and machine learning libraries; **casa** for radio interferometry work; **notebook** for lightweight Jupyter environments; and **desktop** for full Ubuntu desktop sessions with GUI applications.

```bash
# Browse available CANFAR containers
curl -s https://images.canfar.net/api/v2.0/projects/skaha/repositories | \
  jq -r '.[] | .name' | sort

# Check container details
docker inspect images.canfar.net/skaha/astroml:latest
```

For specialized visualization needs, CANFAR provides **carta** for radio astronomy data visualization and **firefly** for optical and infrared data exploration. These containers receive regular updates and official support from the CANFAR team.

### Community-Maintained Containers

The astronomy community contributes specialized containers for emerging tools and workflows. Examples include **marimo** for modern reproducible notebook environments, **vscode** for browser-based code development, and **pluto** for interactive Julia computing. These containers are maintained by community members with oversight from CANFAR.

### Team and Individual Containers

Research groups and individuals can create custom containers for specific projects or workflows. These might include proprietary software, custom analysis pipelines, or specialized configurations needed for particular research programs. While these containers use CANFAR infrastructure, they are maintained by their creators.

```bash
# Example team container structure
images.canfar.net/myproject/custom-pipeline:latest
images.canfar.net/myteam/analysis-env:v2.1
images.canfar.net/user123/specialized-tool:dev
```

---

## Harbor Registry and Distribution

The Harbor registry at `images.canfar.net` serves as the central repository for CANFAR containers. Users can browse available containers, examine metadata and documentation, and access containers for their sessions through the registry interface.

Container versioning follows semantic patterns with `latest` tags for current stable releases, dated tags like `2024.03` for monthly snapshots, and specific commit hashes for development builds. This versioning strategy supports both reproducible research requiring fixed environments and ongoing development needing current software versions.

Access to containers varies by category. CANFAR-supported containers are publicly available to all users. Community-maintained containers may have broader access depending on their purpose and licensing. Team and individual containers can be configured with specific access controls to support proprietary or sensitive work.

---

## Building Custom Containers

Custom container development becomes necessary when existing containers don't meet specific software requirements or when creating standardized environments for research teams. The process involves creating a Dockerfile that defines the software stack, building and testing the container locally, and pushing it to the Harbor registry for use on CANFAR.

### Development Workflow

Successful container development follows an iterative workflow starting with local development and testing. Begin by extending existing CANFAR base images rather than starting from scratch, as this ensures compatibility with the CANFAR runtime environment and includes necessary system configurations.

```bash
# Local development workflow
git clone https://github.com/myteam/custom-container.git
cd custom-container

# Build container locally
docker build -t myteam/analysis-env:latest .

# Test locally with mounted data
docker run -it --rm \
  -v $(pwd)/test-data:/arc/projects/test \
  -v $(pwd)/home:/arc/home/testuser \
  myteam/analysis-env:latest \
  /bin/bash
```

Create your Dockerfile starting from an appropriate base image like `images.canfar.net/skaha/astroml:latest` for astronomy work. Install additional system packages as needed, then switch to the non-root user context for application installations. Python packages should be installed using `pip` or `mamba`, while system-level software requires `apt` or similar package managers during the build process.

### Container Architecture Considerations

All CANFAR containers run on Linux x86_64 architecture and must support the CANFAR user context system. Containers execute as the user who submitted the job, never as root, though they can be configured with sudo access for specific operations during the build process.

The container filesystem integrates with CANFAR storage at runtime. The `/arc` filesystem containing home and project directories is mounted automatically, providing access to persistent data and development code. Temporary high-speed storage is available under `/scratch/` for intensive processing tasks.

When designing containers, separate stable production code that belongs in the container image from development and analysis code that should reside on the `/arc` filesystem. This separation enables easier maintenance and allows users to modify analysis scripts without rebuilding containers.

### Building and Testing Process

Local testing ensures containers work correctly before deployment. Build your container using Docker and test core functionality locally. For notebook containers, verify that Jupyter Lab starts correctly and that key Python packages import properly. Desktop-app containers should be tested to ensure the target application launches and functions as expected.

```dockerfile
# Example notebook container extension
FROM images.canfar.net/skaha/astroml:latest

# Install additional system dependencies
USER root
RUN apt-get update && apt-get install -y \
    gfortran \
    libcfitsio-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch to user context for application installs
USER ${NB_USER}

# Install specialized astronomy packages
RUN pip install --no-cache-dir \
    astroplan \
    photutils \
    reproject

# Set up custom analysis tools
RUN git clone https://github.com/myteam/analysis-tools.git /tmp/analysis-tools && \
    cd /tmp/analysis-tools && \
    pip install --no-cache-dir -e . && \
    rm -rf /tmp/analysis-tools

WORKDIR ${HOME}
```

```dockerfile
# Example headless processing container
FROM images.canfar.net/skaha/astroml:latest

USER root

# Install processing dependencies
RUN apt-get update && apt-get install -y \
    parallel \
    imagemagick \
    ffmpeg \
    && apt-get clean

USER ${NB_USER}

# Install Python processing packages
RUN pip install --no-cache-dir \
    dask[complete] \
    zarr \
    xarray

# Copy processing scripts
COPY --chown=${NB_USER}:${NB_GID} scripts/ /opt/processing/
RUN chmod +x /opt/processing/*.py

# Environment variables for processing
ENV PROCESSING_THREADS=4
ENV OUTPUT_FORMAT=fits

# Default processing entry point
CMD ["python", "/opt/processing/main.py"]
```

```dockerfile
# Example desktop-app container for IRAF
FROM ubuntu:22.04

# Install IRAF and dependencies
USER root
RUN apt-get update && apt-get install -y \
    iraf \
    saods9 \
    xgterm \
    tcsh \
    libx11-6 \
    libxaw7 \
    && apt-get clean

# Create IRAF user setup
RUN useradd -m -s /bin/tcsh iraf
COPY iraf-setup.cl /home/iraf/

# Setup script for CANFAR desktop session
RUN echo '#!/bin/bash\n\
export IRAFARCH=linux64\n\
export TERM=xgterm\n\
cd /arc/home/$USER\n\
exec xgterm -sb -sl 1000 -j -ls -fn 9x15 -title "IRAF" &\n\
exec ds9 &\n\
wait\n' > /usr/local/bin/start-iraf && \
    chmod +x /usr/local/bin/start-iraf

CMD ["/usr/local/bin/start-iraf"]
```

---

## Container Management and Best Practices

Effective container management involves following established patterns for reproducibility, maintainability, and performance. Use specific version tags rather than `latest` for production workflows to ensure consistent environments over time. Layer Docker commands efficiently to minimize image size and build time.

```dockerfile
# Good layering practices
FROM images.canfar.net/skaha/astroml:latest

# Combine related operations
USER root
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    package3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/tmp/*

USER ${NB_USER}

# Pin package versions for reproducibility
RUN pip install --no-cache-dir \
    astroplan==0.8 \
    photutils==1.8.0 \
    reproject==0.10.0

# Use multi-stage builds for complex installations
FROM images.canfar.net/skaha/astroml:latest as builder
COPY source/ /build/
RUN cd /build && make install

FROM images.canfar.net/skaha/astroml:latest
COPY --from=builder /build/bin/* /usr/local/bin/
```

```bash
# Version management
docker tag myproject/tool:latest myproject/tool:v1.2.3
docker tag myproject/tool:latest myproject/tool:2024.03

# Automated builds with GitHub Actions
cat > .github/workflows/build.yml << 'EOF'
name: Build Container
on:
  push:
    tags: ['v*']
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build and push
      run: |
        docker build -t images.canfar.net/myproject/tool:${{ github.ref_name }} .
        docker login images.canfar.net -u ${{ secrets.HARBOR_USER }} -p ${{ secrets.HARBOR_TOKEN }}
        docker push images.canfar.net/myproject/tool:${{ github.ref_name }}
EOF
```

Keep containers focused on their primary purpose rather than creating monolithic images that attempt to solve every possible use case. This approach makes containers easier to maintain and debug while providing clearer upgrade paths.

For team containers, establish clear documentation including purpose, usage examples, and maintenance responsibilities. Version containers systematically and maintain compatibility with CANFAR's evolving infrastructure through regular updates and testing.

```yaml
# Container documentation template (README.md)
# Custom Astronomy Analysis Container

## Purpose
This container provides a specialized environment for X-ray astronomy analysis.

## Usage
```bash
# Launch notebook session
curl -H "Authorization: Bearer $TOKEN" \
  -d "image=images.canfar.net/myteam/xray-analysis:latest" \
  -d "type=notebook" \
  https://ws-uv.canfar.net/skaha/v0/session
```

## Included Software
- XSPEC 12.12.1
- PyXspec
- Custom analysis tools v2.1

## Maintenance
- Maintainer: team@institution.edu
- Update schedule: Monthly
- Source: https://github.com/myteam/xray-container
```

Regular maintenance includes updating base images, refreshing software dependencies, and testing compatibility with new CANFAR features. Community-maintained containers benefit from collaborative development practices including shared repositories and issue tracking.

---

## Integration with CANFAR Workflows

Containers integrate seamlessly with CANFAR's interactive sessions and batch processing systems. Interactive sessions launch containers with full access to mounted storage and appropriate resource allocations. Batch jobs use headless containers for automated processing with results written back to persistent storage.

The container system supports different resource configurations including CPU, memory, and GPU allocations based on computational requirements. GPU-enabled containers like **astroml-cuda** automatically gain access to GPU resources when launched on appropriate hardware nodes.

Session persistence allows users to return to running containers across browser sessions while maintaining computational state. However, containers themselves are ephemeral - when sessions end, any changes made within the container filesystem are lost. This design encourages proper separation between stable container environments and dynamic analysis code.

Understanding this integration helps optimize workflows by leveraging container strengths while working within system constraints. Plan computational workflows to use containers for consistent software environments while storing results, code, and data on the persistent `/arc` filesystem.

---

*Continue exploring CANFAR capabilities through [Interactive Sessions](guides/interactive-sessions/index.md) for hands-on container usage, [Batch Jobs](batch-jobs.md) for automated processing, or [Storage Management](guides/storage/index.md) for data organization strategies.*
