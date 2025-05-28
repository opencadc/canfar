# Container Building Guide

> **📚 Related Guides:**
>
> - [Storage Systems Guide →](storage-systems-guide.md) - Understanding container data access patterns
> - [Headless Execution Guide →](headless-execution-guide.md) - Running containers in batch mode
> - [Data Transfer Guide →](data-transfer-guide.md) - Moving data for container development
> - [Choose Your Interface →](getting-started/choose-interface.md) - Understanding container session types

This guide covers how to build different types of containers for the CANFAR Science Platform, including notebooks, desktop applications, and headless containers.

## Container Types Overview

The CANFAR Science Platform supports three main container types:

### 1. Notebook Containers

- **Purpose**: Interactive Jupyter environments for data analysis
- **Base Images**: Typically based on `jupyter/scipy-notebook` or similar
- **Access**: Through web browser as native HTML5 applications
- **Requirements**: Must have `jupyter lab` executable available

### 2. Desktop-App Containers

- **Purpose**: GUI applications requiring X11 display
- **Base Images**: Desktop environments with VNC support
- **Access**: Through VNC client or web-based noVNC interface
- **Requirements**: X11 support, VNC server, default executable is `xterm`
- **Note**: Desktop-app containers are launched within desktop sessions

### 3. Headless Containers

- **Purpose**: Batch processing and automation without GUI
- **Base Images**: Any Linux distribution
- **Access**: Command-line execution, no interactive interface
- **Requirements**: Must be labeled as `headless` in Harbor registry

### 4. Contributed Containers

- **Purpose**: Community-developed tools and specialized applications
- **Base Images**: Various, depending on the tool
- **Access**: Through the Science Portal contributed session type
- **Requirements**: Web interface typically on port 5000

!!! info "CANFAR Team Supported Applications"
    The CANFAR team actively supports and maintains:
    
    - **Desktop Sessions** (full Linux desktop environment with VNC)
    - **CARTA** (radio astronomy visualization tool)
    - **Firefly** (astronomical image and catalog viewer)
    
    Desktop-app containers (individual GUI applications) are contributed by the community.

## Universal Requirements

All CANFAR containers must meet these minimum requirements:

- **Architecture**: Linux x86_64 distribution
- **User Context**: Containers run as the CADC user, never as root
- **Runtime Root**: If root access needed, configure sudo for specific actions during build
- **File System**: `/arc` filesystem automatically mounted for data access (see [Storage Systems Guide](storage-systems-guide.md))

## Building Notebook Containers

### Basic Structure

```dockerfile
# Start with Jupyter base image
ARG ROOT_CONTAINER=jupyter/scipy-notebook:latest
FROM ${ROOT_CONTAINER}

LABEL maintainer="Your Name <your.email@institution.ca>"

USER root
WORKDIR /tmp

# System package updates
RUN apt-get update --yes --quiet --fix-missing \
    && apt-get upgrade --yes --quiet

# Install system packages
COPY packages.apt .
RUN apt-get install --yes --quiet $(cat packages.apt) \
    && apt-get clean --yes \
    && apt-get autoremove --purge --quiet --yes \
    && rm -rf /var/lib/apt/lists/* /var/tmp/*

# Configure system for CANFAR
ADD nsswitch.conf /etc/

USER ${NB_USER}

# Update conda environment
COPY env.yml .
RUN mamba env update --quiet -n base --file env.yml \
    && mamba update --quiet --all --yes \
    && mamba clean --all --quiet --force --yes \
    && fix-permissions ${CONDA_DIR} \
    && fix-permissions /home/${NB_USER}

WORKDIR ${HOME}
```

### Required Files

**packages.apt** - System packages to install:
```
sssd-client
acl
vim
curl
wget
```

**nsswitch.conf** - For proper user lookup:
```
passwd:     files sss
group:      files sss
shadow:     files sss
hosts:      files dns
networks:   files
protocols:  files
services:   files sss
netgroup:   files sss
automount:  files sss
```

**env.yml** - Conda environment specification:
```yaml
name: base
channels:
  - conda-forge
  - defaults
dependencies:
  - astropy
  - matplotlib
  - numpy
  - scipy
  - pandas
  - pip
  - pip:
    - vos
    - cadcdata
    - cadctap
```

### Notebook-Specific Features

Before activating the mamba environment, always run:
```bash
mamba activate base
```

Use `python` instead of `python3` in all documentation and examples.

## Building Desktop-App Containers

### VNC-Based Desktop Structure

```dockerfile
FROM ubuntu:22.04

# Install desktop environment and VNC
RUN apt-get update && apt-get install -y \
    xfce4 \
    xfce4-terminal \
    tigervnc-standalone-server \
    tigervnc-viewer \
    novnc \
    websockify \
    supervisor \
    curl \
    wget \
    && apt-get clean

# Install application-specific software
RUN apt-get install -y your-gui-application

# Configure VNC environment
ENV DISPLAY=:1 \
    VNC_PORT=5901 \
    NO_VNC_PORT=6901 \
    VNC_RESOLUTION=1280x1024 \
    VNC_PW=vncpassword

# Copy VNC configuration files
COPY conf/vnc_custom.html $NO_VNC_HOME/index.html
COPY conf/base_custom.css $NO_VNC_HOME/app/styles/

# System configuration for CANFAR
RUN apt-get install -y sssd-client acl
COPY nsswitch.conf /etc/
RUN echo "Set disable_coredump false" > /etc/sudo.conf
RUN dbus-uuidgen --ensure

# Set up startup scripts
COPY startup.sh /skaha/startup.sh
RUN chmod +x /skaha/startup.sh

EXPOSE $VNC_PORT $NO_VNC_PORT

CMD ["/skaha/startup.sh"]
```

### Desktop Application Requirements

- **Default Command**: Must start `xterm` by default
- **VNC Server**: Required for remote desktop access
- **Window Manager**: XFCE4 recommended for compatibility
- **Font Support**: Install fonts for your specific application

### Example: CASA Desktop Container

```dockerfile
FROM ubuntu:20.04

# Install CASA and dependencies
RUN apt-get update && apt-get install -y \
    casa-data \
    xterm \
    xfce4 \
    tigervnc-standalone-server

# Configure CASA environment
ENV CASA_ROOT=/opt/casa
ENV PATH=$CASA_ROOT/bin:$PATH

# Set up desktop environment
COPY init.sh /skaha/
RUN chmod +x /skaha/init.sh

CMD ["/skaha/init.sh"]
```

## Building Headless Containers

### Basic Headless Structure

```dockerfile
FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    wget \
    && apt-get clean

# Install your processing software
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Configure for CANFAR
RUN apt-get install -y sssd-client acl
COPY nsswitch.conf /etc/
RUN echo "Set disable_coredump false" > /etc/sudo.conf

# Copy processing scripts
COPY src/ /opt/processing/
RUN chmod +x /opt/processing/*.sh

# Default command (will be overridden by skaha)
CMD ["/bin/bash"]
```

### Headless Container Best Practices

- **Stateless**: Design for single-use execution
- **Logging**: Write output to stdout/stderr for monitoring
- **Exit Codes**: Return proper exit codes (0 for success, non-zero for failure)
- **File Handling**: Read from/write to `/arc` filesystem paths (see [Storage Guide](storage-systems-guide.md))
- **Environment**: Check for required environment variables
- **Scratch Usage**: Use `/scratch/` for temporary high-speed processing (see [Headless Execution Guide](headless-execution-guide.md))

### Example Processing Script

```bash
#!/bin/bash
set -e  # Exit on error

# Check required environment variables
if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_DIR" ]; then
    echo "Error: INPUT_FILE and OUTPUT_DIR must be set"
    exit 1
fi

# Activate conda environment if needed
mamba activate base

# Run processing
echo "Processing $INPUT_FILE..."
python /opt/processing/analyze.py \
    --input "$INPUT_FILE" \
    --output "$OUTPUT_DIR/results.fits" \
    --verbose

echo "Processing complete!"
exit 0
```

## Container Initialization

### Startup Scripts

#### `/skaha/init.sh` (Non-blocking)

For containers needing runtime initialization:

```bash
#!/bin/bash
# Non-blocking initialization script

# Set up environment
export MYAPP_CONFIG=/arc/home/$USER/.myapp/config

# Create directories
mkdir -p $MYAPP_CONFIG

# Initialize configuration
if [ ! -f $MYAPP_CONFIG/app.conf ]; then
    cp /opt/myapp/default.conf $MYAPP_CONFIG/app.conf
fi

# MUST NOT BLOCK - return control immediately
```

#### `/skaha/startup.sh` (Environment Setup)

For containers needing environment setup before execution:

```bash
#!/bin/bash
# Startup script that sets environment and executes command

# Set up application environment
source /opt/myapp/setup.sh
export PATH=/opt/myapp/bin:$PATH

# Execute the command passed to this script
exec "$@"
```

## Building and Testing

### Local Testing

1. **Build the container**:

   ```bash
   docker build -t my-container:test .
   ```

2. **Test notebook containers**:

   ```bash
   docker run -p 8888:8888 my-container:test
   ```

3. **Test desktop containers**:

   ```bash
   docker run -p 6901:6901 my-container:test
   # Access via http://localhost:6901/?password=vncpassword
   ```

4. **Test headless containers**:

   ```bash
   docker run -it my-container:test /bin/bash
   ```

### Publishing to Harbor

1. **Tag for Harbor**:

   ```bash
   docker tag my-container:test images.canfar.net/myproject/my-container:1.0
   ```

2. **Login to Harbor**:

   ```bash
   docker login images.canfar.net
   ```

3. **Push to registry**:

   ```bash
   docker push images.canfar.net/myproject/my-container:1.0
   ```

4. **Label in Harbor UI**:

   - Go to <https://images.canfar.net>
   - Navigate to your image
   - Add appropriate labels: `notebook`, `desktop-app`, or `headless`

## Common Issues and Troubleshooting

### Permission Issues

- Ensure containers don't run as root
- Use proper file permissions for `/skaha` scripts
- Configure sudo only for specific operations

### Environment Variables

- Don't hardcode paths - use environment variables
- Check for required variables in startup scripts
- Use `/arc` paths for persistent data

### Resource Management

- Don't include unnecessary packages to keep images small
- Clean package caches and temporary files
- Use multi-stage builds when appropriate

### VNC Configuration

- Test VNC connectivity before publishing
- Ensure proper display resolution settings
- Verify noVNC web interface works

## Advanced Topics

### Multi-Stage Builds

For complex applications with large build dependencies:

```dockerfile
# Build stage
FROM ubuntu:22.04 as builder
RUN apt-get update && apt-get install -y build-essential
COPY src/ /build/
RUN make -C /build install

# Runtime stage  
FROM ubuntu:22.04
COPY --from=builder /build/bin/* /usr/local/bin/
# ... rest of runtime configuration
```

### Custom Base Images

Create reusable base images for your organization:

```dockerfile
FROM ubuntu:22.04
# Common CANFAR configuration
RUN apt-get update && apt-get install -y sssd-client acl
COPY nsswitch.conf /etc/
RUN echo "Set disable_coredump false" > /etc/sudo.conf
# Tag as: images.canfar.net/myorg/base:latest
```

### Performance Optimization

- Use BuildKit for faster builds
- Leverage Docker layer caching
- Minimize layer count where possible
- Use specific package versions for reproducibility

This guide provides the foundation for building all types of containers for the CANFAR Science Platform. Always test thoroughly before publishing to ensure compatibility with the platform infrastructure.

---

**Related Documentation:**

- [Headless Execution Guide](headless-execution-guide.md) - Run your custom containers in batch mode
- [Storage Systems Guide](storage-systems-guide.md) - Optimize container data access patterns  
- [Data Transfer Guide](data-transfer-guide.md) - Move data for container development and testing
- [Harbor Registry Documentation](https://goharbor.io/docs/) - Container registry management
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/) - Docker official guidelines
