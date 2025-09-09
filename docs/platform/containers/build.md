# Building Custom Containers

**Creating your own astronomy software environments for CANFAR - from development through deployment and maintenance.**

!!! info "Platform Navigation"
    **Container Building**: Creating custom software environments for specialised research workflows.  
    **[Containers Home](index.md)** | **[Registry Management](registry.md)** | **[Platform Home](../index.md)**

!!! abstract "🎯 Container Building Overview"
    **Master custom container development:**
    
    - **Development Setup**: Local environments for container building and testing
    - **CANFAR Requirements**: Platform-specific configurations and best practices
    - **Testing & Debugging**: Ensuring containers work correctly in CANFAR sessions
    - **Harbor Registry**: Publishing and maintaining custom containers

Building custom containers becomes necessary when existing CANFAR containers don't meet your specific software requirements or when creating standardised environments for research teams. This guide covers the complete development workflow from initial setup through deployment and maintenance.

## 📋 When to Build Custom Containers

### Scenarios Requiring Custom Containers

**Missing Software Packages:**
- Proprietary or licensed software not available in public containers
- Cutting-edge research tools not yet in CANFAR containers
- Specific versions of software required for reproducibility
- Legacy software with complex dependency requirements

**Team Standardisation:**
- Consistent environments across research groups
- Custom analysis pipelines and workflows
- Institutional software licensing requirements
- Project-specific data processing tools

**Performance Optimisation:**
- GPU-optimised builds for specific hardware
- Memory-efficient configurations for large datasets
- Custom compilation flags for scientific software
- Minimised container size for batch processing

### Alternatives to Consider First

Before building custom containers, consider these alternatives:

```bash
# Runtime package installation (temporary)
pip install --user new-package          # Installs to /arc/home/user/.local/
conda install -c conda-forge package    # If conda is available

# Development in existing containers
# Use astroml as base and install packages per session
# Keep development scripts in /arc/home/ or /arc/projects/
```

!!! tip "Start Simple"
    Try adding software to existing containers at runtime first. Only build custom containers when you need permanent, reproducible environments or when runtime installation isn't feasible.

## 🛠️ Development Environment Setup

### Local Development Prerequisites

**Required software:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine
- Git for version control
- Text editor or IDE (VS Code recommended for Dockerfile support)
- Terminal access for command-line operations

**CANFAR-specific requirements:**
- Harbor registry access ([images.canfar.net](https://images.canfar.net/))
- Understanding of CANFAR storage mounting (`/arc/`, `/scratch/`)
- Knowledge of target session types (notebook, desktop-app, headless)

### Development Workflow Setup

Create a structured development environment:

```bash
# Set up development directory
mkdir ~/canfar-containers
cd ~/canfar-containers

# Create container project
mkdir my-analysis-container
cd my-analysis-container

# Initialize version control
git init
git remote add origin https://github.com/myteam/my-analysis-container.git

# Create basic structure
touch Dockerfile
touch README.md
mkdir scripts/
mkdir tests/
mkdir docs/

# Create test data directories (for local testing)
mkdir test-data/
mkdir test-home/
```

**Recommended project structure:**
```
my-analysis-container/
├── Dockerfile              # Container definition
├── README.md               # Documentation and usage
├── requirements.txt        # Python dependencies
├── environment.yml         # Conda environment (if using)
├── scripts/               # Custom scripts to include
├── tests/                 # Container functionality tests
├── docs/                  # Additional documentation
├── test-data/             # Sample data for testing
├── test-home/             # Mock user home for testing
└── .github/workflows/     # CI/CD automation (optional)
```

## 🏗️ Container Development Process

### Starting from CANFAR Base Images

Always extend existing CANFAR base images rather than starting from scratch:

```dockerfile
# For general astronomy work
FROM images.canfar.net/skaha/astroml:latest

# For radio astronomy
FROM images.canfar.net/skaha/casa:latest

# For minimal environments
FROM images.canfar.net/skaha/notebook:latest

# For desktop applications
FROM ubuntu:22.04  # Only if creating completely new desktop-app
```

### Basic Dockerfile Patterns

#### Notebook Container Extension

```dockerfile
FROM images.canfar.net/skaha/astroml:latest

# Container metadata
LABEL maintainer="research-team@university.edu"
LABEL description="Custom astronomy analysis environment with X-ray tools"
LABEL version="1.0.0"

# Install system dependencies as root
USER root

# Update package lists and install system packages
RUN apt-get update && apt-get install -y \
    gfortran \
    libcfitsio-dev \
    libwcs-dev \
    cmake \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /var/tmp/*

# Switch back to non-root user for application installs
USER ${NB_USER}

# Install Python packages
RUN pip install --no-cache-dir \
    astroplan==0.9.1 \
    photutils==1.10.0 \
    reproject==0.13.0 \
    specutils==1.12.0 \
    regions==0.8

# Install specialized X-ray analysis tools
RUN pip install --no-cache-dir \
    xspec-models-cxc \
    pyxspec \
    sherpa

# Install custom analysis tools from source
RUN git clone https://github.com/myteam/xray-analysis-tools.git /tmp/tools && \
    cd /tmp/tools && \
    pip install --no-cache-dir -e . && \
    rm -rf /tmp/tools

# Copy custom scripts and configurations
COPY --chown=${NB_USER}:${NB_GID} scripts/ /opt/custom-tools/
COPY --chown=${NB_USER}:${NB_GID} configs/ /opt/configs/

# Set up environment variables
ENV XRAY_TOOLS_PATH=/opt/custom-tools
ENV PYTHONPATH=${PYTHONPATH}:/opt/custom-tools

# Set working directory
WORKDIR ${HOME}

# Ensure Jupyter can find custom tools
RUN jupyter lab build --dev-build=False --minimize=False
```

#### Desktop-App Container

```dockerfile
FROM ubuntu:22.04

# Avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # X11 and GUI libraries
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxrandr2 \
    libxss1 \
    libgtk-3-0 \
    # Application-specific dependencies
    ds9 \
    saods9 \
    xterm \
    # Basic tools
    wget \
    curl \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create startup script for CANFAR desktop integration
RUN mkdir -p /skaha

# Create the startup script
RUN echo '#!/bin/bash\n\
# Set up X11 environment\n\
export DISPLAY=${DISPLAY:-:1}\n\
\n\
# Navigate to user home directory\n\
cd /arc/home/$USER || cd /tmp\n\
\n\
# Launch the application\n\
exec ds9 -title "Custom DS9 - $USER" &\n\
\n\
# Keep container running\n\
wait\n' > /skaha/startup.sh

# Make startup script executable
RUN chmod +x /skaha/startup.sh

# Set the startup script as entrypoint
ENTRYPOINT ["/skaha/startup.sh"]
```

#### Headless Processing Container

```dockerfile
FROM images.canfar.net/skaha/astroml:latest

USER root

# Install processing tools
RUN apt-get update && apt-get install -y \
    # Parallel processing tools
    parallel \
    # Image processing
    imagemagick \
    # Video processing
    ffmpeg \
    # Archive tools
    zip \
    unzip \
    # Performance monitoring
    htop \
    iotop \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER ${NB_USER}

# Install Python packages for large-scale processing
RUN pip install --no-cache-dir \
    # Distributed computing
    dask[complete] \
    # High-performance I/O
    zarr \
    h5py \
    # Data formats
    xarray \
    astropy-healpix \
    # Workflow management
    snakemake \
    # Performance monitoring
    psutil

# Copy processing scripts
COPY --chown=${NB_USER}:${NB_GID} processing/ /opt/processing/

# Set up processing environment
ENV PROCESSING_THREADS=4
ENV PROCESSING_MEMORY_LIMIT=8GB
ENV OUTPUT_FORMAT=fits
ENV TEMP_DIR=/scratch

# Make scripts executable
RUN chmod +x /opt/processing/*.py /opt/processing/*.sh

# Default command for batch execution
CMD ["python", "/opt/processing/main.py"]
```

### Advanced Container Features

#### Multi-stage Builds for Complex Software

```dockerfile
# Build stage for compiling software
FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libfftw3-dev \
    libcfitsio-dev

# Clone and build complex software
RUN git clone https://github.com/radio-astro/complex-software.git /src
WORKDIR /src
RUN cmake . && make -j$(nproc) && make install

# Production stage
FROM images.canfar.net/skaha/astroml:latest

# Copy only the built binaries
COPY --from=builder /usr/local/bin/complex-software /usr/local/bin/
COPY --from=builder /usr/local/lib/libcomplex* /usr/local/lib/

# Update library cache
USER root
RUN ldconfig
USER ${NB_USER}
```

#### GPU-Enabled Containers

```dockerfile
FROM images.canfar.net/skaha/astroml-cuda:latest

# Install additional GPU-accelerated packages
RUN pip install --no-cache-dir \
    # GPU-accelerated arrays
    cupy-cuda11x \
    # GPU machine learning
    rapids-singlecell \
    # GPU image processing
    cucim \
    # GPU signal processing
    cusignal

# Install custom CUDA code
COPY --chown=${NB_USER}:${NB_GID} cuda_kernels/ /opt/cuda_kernels/
RUN cd /opt/cuda_kernels && \
    nvcc -o gpu_analysis analysis.cu -lcufft -lcublas
```

## 🧪 Testing and Debugging

### Local Testing Strategy

Test containers thoroughly before deploying to CANFAR:

```bash
# Build container locally
docker build -t myteam/analysis-env:test .

# Test basic functionality
docker run --rm myteam/analysis-env:test python -c "import astropy; print('Astropy works!')"

# Test with mounted directories (simulate CANFAR environment)
docker run -it --rm \
  -v $(pwd)/test-data:/arc/projects/test \
  -v $(pwd)/test-home:/arc/home/testuser \
  -e USER=testuser \
  -e HOME=/arc/home/testuser \
  myteam/analysis-env:test \
  /bin/bash
```

### Testing Notebook Containers

```bash
# Test Jupyter startup
docker run -it --rm \
  -p 8888:8888 \
  -v $(pwd)/test-notebooks:/arc/home/testuser \
  -e USER=testuser \
  myteam/analysis-env:test \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```

### Testing Desktop-App Containers

```bash
# Test X11 application (requires X11 forwarding setup)
docker run -it --rm \
  -e DISPLAY=${DISPLAY} \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  myteam/desktop-app:test \
  xterm
```

### Automated Testing Framework

Create test scripts to validate container functionality:

```python
# tests/test_container.py
import subprocess
import pytest

def test_python_packages():
    """Test that required Python packages are installed."""
    packages = ['astropy', 'numpy', 'scipy', 'matplotlib']
    
    for package in packages:
        result = subprocess.run([
            'docker', 'run', '--rm', 'myteam/analysis-env:test',
            'python', '-c', f'import {package}; print(f"{package} version: {{package.__version__}}")'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Package {package} not available"
        print(result.stdout)

def test_custom_scripts():
    """Test that custom analysis scripts work."""
    result = subprocess.run([
        'docker', 'run', '--rm', 'myteam/analysis-env:test',
        'python', '/opt/custom-tools/test_analysis.py'
    ], capture_output=True, text=True)
    
    assert result.returncode == 0, "Custom analysis script failed"
    assert "Analysis completed" in result.stdout

def test_file_permissions():
    """Test that file permissions work correctly."""
    result = subprocess.run([
        'docker', 'run', '--rm',
        '-v', '$(pwd)/test-data:/arc/projects/test',
        'myteam/analysis-env:test',
        'ls', '-la', '/arc/projects/test'
    ], capture_output=True, text=True)
    
    assert result.returncode == 0, "Cannot access mounted directories"

if __name__ == "__main__":
    pytest.main([__file__])
```

### Debugging Common Issues

#### Permission Problems

```dockerfile
# Ensure proper user context
USER root
# ... install system packages ...

# Switch to non-root user
USER ${NB_USER}
# ... install user packages ...

# Set proper ownership for copied files
COPY --chown=${NB_USER}:${NB_GID} scripts/ /opt/scripts/
```

#### Package Installation Failures

```dockerfile
# Clean package caches to reduce image size and avoid corruption
RUN apt-get update && apt-get install -y package1 package2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /var/tmp/*

# Pin package versions to avoid conflicts
RUN pip install --no-cache-dir \
    astropy==5.3.4 \
    numpy==1.24.3 \
    scipy==1.10.1
```

#### Container Size Issues

```dockerfile
# Use multi-stage builds
FROM ubuntu:22.04 AS builder
# ... build software ...

FROM images.canfar.net/skaha/astroml:latest
COPY --from=builder /output /final-location

# Minimize layers
RUN apt-get update && apt-get install -y pkg1 pkg2 pkg3 && apt-get clean && rm -rf /var/lib/apt/lists/*
# Instead of:
# RUN apt-get update
# RUN apt-get install -y pkg1
# RUN apt-get install -y pkg2
```

## 📦 Building and Optimization

### Efficient Docker Practices

#### Layer Optimisation

```dockerfile
# Good: Combine related operations
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    package3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Good: Order layers by change frequency
FROM base-image
# System packages (change rarely)
RUN apt-get update && apt-get install -y system-packages
# Python packages (change occasionally)  
RUN pip install stable-packages
# Custom code (changes frequently)
COPY . /app/
```

#### Size Minimisation

```dockerfile
# Use .dockerignore to exclude unnecessary files
# .dockerignore contents:
# .git
# *.md
# tests/
# docs/
# .DS_Store
# __pycache__

# Clean up in same layer
RUN apt-get update && apt-get install -y packages \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Use --no-cache-dir for pip
RUN pip install --no-cache-dir package-name
```

### Performance Optimisation

#### Parallel Builds

```bash
# Build with multiple cores
docker build --build-arg MAKEFLAGS=-j$(nproc) .

# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker build .
```

#### Build Arguments for Flexibility

```dockerfile
# Flexible package versions
ARG PYTHON_VERSION=3.11
ARG ASTROPY_VERSION=5.3.4

FROM python:${PYTHON_VERSION}-slim

RUN pip install --no-cache-dir astropy==${ASTROPY_VERSION}
```

```bash
# Build with custom arguments
docker build --build-arg PYTHON_VERSION=3.10 --build-arg ASTROPY_VERSION=5.2.0 .
```

### Version Management and Tagging

```bash
# Build with specific tags
docker build -t myteam/analysis-env:latest .
docker build -t myteam/analysis-env:v1.2.3 .
docker build -t myteam/analysis-env:2024.03 .

# Tag for Harbor registry
docker tag myteam/analysis-env:latest images.canfar.net/myteam/analysis-env:latest
docker tag myteam/analysis-env:v1.2.3 images.canfar.net/myteam/analysis-env:v1.2.3
```

## 🚀 Publishing to Harbor Registry

### Registry Authentication

```bash
# Login to CANFAR Harbor registry
docker login images.canfar.net

# Or use credentials directly
echo "your-harbor-password" | docker login images.canfar.net -u your-harbor-username --password-stdin
```

### Pushing Images

```bash
# Push specific version
docker push images.canfar.net/myteam/analysis-env:v1.2.3

# Push latest
docker push images.canfar.net/myteam/analysis-env:latest

# Push all tags
docker push --all-tags images.canfar.net/myteam/analysis-env
```

### Container Labeling for CANFAR

Ensure proper labeling for session type integration:

```dockerfile
# For notebook containers
LABEL ca.nrc.cadc.skaha.type="notebook"

# For desktop-app containers  
LABEL ca.nrc.cadc.skaha.type="desktop-app"

# For contributed applications
LABEL ca.nrc.cadc.skaha.type="contributed"

# Additional metadata
LABEL maintainer="research-team@university.edu"
LABEL version="1.2.3"
LABEL description="Custom X-ray astronomy analysis environment"
LABEL documentation="https://github.com/myteam/container-docs"
```

## 🔄 Maintenance and Updates

### Update Strategy

#### Regular Maintenance Schedule

```bash
#!/bin/bash
# update-container.sh - Monthly maintenance script

# Update base image
docker pull images.canfar.net/skaha/astroml:latest

# Rebuild container
docker build --no-cache -t myteam/analysis-env:$(date +%Y.%m) .

# Test new build
./run-tests.sh myteam/analysis-env:$(date +%Y.%m)

# If tests pass, tag as latest
docker tag myteam/analysis-env:$(date +%Y.%m) myteam/analysis-env:latest

# Push updates
docker push myteam/analysis-env:$(date +%Y.%m)
docker push myteam/analysis-env:latest
```

#### Dependency Updates

```dockerfile
# Pin major versions, allow minor updates
RUN pip install --no-cache-dir \
    'astropy>=5.3,<6.0' \
    'numpy>=1.24,<2.0' \
    'scipy>=1.10,<2.0'

# For critical reproducibility, pin exact versions
RUN pip install --no-cache-dir \
    astropy==5.3.4 \
    numpy==1.24.3 \
    scipy==1.10.1
```

### CI/CD Integration

#### GitHub Actions for Automated Builds

```yaml
# .github/workflows/build-container.yml
name: Build and Push Container

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
      
    - name: Login to Harbor Registry
      uses: docker/login-action@v3
      with:
        registry: images.canfar.net
        username: ${{ secrets.HARBOR_USERNAME }}
        password: ${{ secrets.HARBOR_TOKEN }}
        
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: images.canfar.net/myteam/analysis-env
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        push: ${{ github.event_name != 'pull_request' }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        
    - name: Test container
      run: |
        docker run --rm ${{ steps.meta.outputs.tags }} python -c "import astropy; print('Container test passed')"
```

### Documentation and User Support

#### Container Documentation Template

```markdown
# Custom Analysis Environment

## Overview
This container provides a specialized environment for X-ray astronomy analysis with the following additions to the base astroml container:

- XSPEC and PyXspec for spectral analysis
- Custom data reduction pipeline
- Specialized plotting and analysis tools

## Usage

### Notebook Session
```bash
canfar create notebook images.canfar.net/myteam/xray-analysis:latest \
  --name "xray-analysis" --cores 4 --memory 16
```

### Desktop Session
```bash
canfar create desktop images.canfar.net/myteam/xray-analysis:latest \
  --name "xray-desktop" --cores 4 --memory 16
```

## Included Software

### System Packages
- gfortran: Fortran compiler for XSPEC
- libcfitsio-dev: FITS file handling

### Python Packages
- astroplan (0.9.1): Observation planning
- photutils (1.10.0): Photometry tools
- pyxspec: Python interface to XSPEC

### Custom Tools
- `/opt/custom-tools/`: Custom analysis scripts
- `/opt/configs/`: Default configuration files

## Development

### Building Locally
```bash
git clone https://github.com/myteam/xray-container.git
cd xray-container
docker build -t myteam/xray-analysis:dev .
```

### Testing
```bash
./run-tests.sh
```

## Support

- **Issues**: [GitHub Issues](https://github.com/myteam/xray-container/issues)
- **Documentation**: [Project Wiki](https://github.com/myteam/xray-container/wiki)
- **Contact**: research-team@university.edu

## Changelog

### v1.2.3 (2024-03-15)
- Updated astroplan to 0.9.1
- Added custom spectral analysis tools
- Fixed XSPEC configuration issues

### v1.2.2 (2024-02-15)
- Updated base image to astroml:2024.02
- Security updates for system packages
```

## 🆘 Troubleshooting

### Common Build Issues

#### Package Installation Failures

```bash
# Debug package installation
docker run -it --rm images.canfar.net/skaha/astroml:latest /bin/bash
# Try installing packages manually to identify issues

# Check available package versions
apt-cache search package-name
apt-cache policy package-name
```

#### Permission Denied Errors

```dockerfile
# Ensure correct user context
USER root
RUN apt-get install -y packages
USER ${NB_USER}
RUN pip install --user packages

# Fix file ownership
COPY --chown=${NB_USER}:${NB_GID} files/ /destination/
```

#### Container Won't Start on CANFAR

```bash
# Check container labels
docker inspect images.canfar.net/myteam/container:latest | grep -A 10 Labels

# Test startup command
docker run -it --rm images.canfar.net/myteam/container:latest /bin/bash

# For desktop-app containers, test startup script
docker run -it --rm images.canfar.net/myteam/container:latest /skaha/startup.sh
```

### Performance Issues

#### Large Container Size

```bash
# Analyze container size
docker images | grep myteam/container
docker history myteam/container:latest

# Use dive tool for detailed analysis
dive myteam/container:latest
```

#### Slow Build Times

```bash
# Use build cache effectively
docker build --cache-from=myteam/container:latest .

# Enable BuildKit
export DOCKER_BUILDKIT=1
docker build .

# Use multi-stage builds to reduce final size
```

### Runtime Issues

#### Package Import Failures

```python
# Test package installation in running container
import sys
print(sys.path)

# Check package location
import package_name
print(package_name.__file__)

# Verify environment variables
import os
print(os.environ.get('PYTHONPATH'))
```

#### Storage Access Problems

```bash
# Test storage mounting (local testing)
docker run -it --rm \
  -v /path/to/test:/arc/projects/test \
  -e USER=testuser \
  myteam/container:latest \
  ls -la /arc/projects/test
```
