# Building Custom Containers

**Creating your own astronomy software environments for CANFAR - from development through deployment and maintenance.**

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

**Team Standardization:**
- Consistent environments across research groups
- Custom analysis pipelines and workflows
- Institutional software licensing requirements
- Project-specific data processing tools

**Performance Optimization:**
- GPU-optimised builds for specific hardware
- Memory-efficient configurations for large datasets
- Custom compilation flags for scientific software
- Minimized container size for batch processing

### Alternatives to Consider First

Before building custom containers, consider these alternatives:

```bash
# Runtime package installation (temporary)
pip install --user new-package          # Installs to /arc/home/[user]/.local/
mamba install -c conda-forge package    # If mamba or conda is available

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
FROM images.canfar.net/skaha/base:latest

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

# Set up environment variables
ENV XRAY_TOOLS_PATH=/opt/custom-tools
ENV PYTHONPATH=${PYTHONPATH}:/opt/custom-tools

```

#### Desktop-App Container

```dockerfile
FROM ubuntu:24.04

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
    saods9 \
    xterm \
    wget \
    curl \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create startup script for CANFAR desktop integration
RUN mkdir -p /skaha

# Create the startup script
COPY startup.sh /skaha/ 

# Make startup script executable
RUN chmod +x /skaha/startup.sh

# Set the startup script as entrypoint
ENTRYPOINT ["/skaha/startup.sh"]
```

with the `startup.sh` being:

```bash
#!/bin/bash

# Set up X11 environment
export DISPLAY=${DISPLAY:-:1}

# Navigate to user home directory
cd /arc/home/$USER || cd /tmp

# Launch the application
exec ds9 -title "Custom DS9 - $USER" &

# Keep container running
wait
```

### Advanced Container Features

#### Multi-stage Builds for Complex Software

```dockerfile
# Build stage for compiling software
FROM ubuntu:24.04 AS builder

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


#### Package Installation Failures

```dockerfile
# Clean package caches to reduce image size and avoid corruption
RUN apt-get update && apt-get install -y package1 package2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /var/tmp/*

# if necessary, you can pin exact package versions to avoid conflicts
RUN pip install --no-cache-dir \
    astropy==5.3.4 \
    numpy==1.24.3 \
    scipy==1.10.1
```

#### Container Size Issues

```dockerfile
# Use multi-stage builds
FROM ubuntu:24.04 AS builder
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

#### Layer Optimization

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

#### Size Minimization

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

### Performance Optimization

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
