# Container Development Guide

Learn how to build, test, and publish custom containers for the CANFAR Science Platform.

## 🐳 Container Basics

### What are Containers?
Containers package your software with all its dependencies, ensuring it runs consistently across different environments. CANFAR uses Docker containers to provide isolated, reproducible computing environments.

### Why Build Custom Containers?
- **Specialized software**: Include tools not available in standard containers
- **Specific versions**: Pin exact library versions for reproducibility
- **Custom workflows**: Create containers tailored to your research pipeline
- **Team collaboration**: Share consistent environments with collaborators

---

## 🚀 Quick Start

### Prerequisites
- Access to [CANFAR Container Registry](https://images.canfar.net)
- Basic familiarity with Docker
- CADC account with container publishing permissions

### Your First Container
```dockerfile
# Dockerfile
FROM images.canfar.net/skaha/astroml:latest

# Install additional packages
RUN mamba install your-package

# Add your analysis scripts
COPY scripts/ /opt/scripts/
RUN chmod +x /opt/scripts/*

# Set working directory
WORKDIR /arc/projects

# Default command
CMD ["/bin/bash"]
```

---

## 📋 Container Requirements

### Base Images
You can start from CANFAR-compatible base images:

```dockerfile
# Recommended base images
FROM images.canfar.net/skaha/astroml:latest       # Python + astronomy + jupyterlab + xterm
FROM images.canfar.net/skaha/base:latest          # minimal python+conda
```

### Features
At run time, the container will:
- **Run as non-root user**: it will run as your CADC user (uid and gid)
- **Support `/arc` mount point** for shared storage access
- **Support `/scratch` mount point** for fast, non-shared, temporary storage
- **Handle DISPLAY environment** for GUI applications

---

## 🛠️ Building Containers

### Local Development
```bash
# Build your container
docker build -t myproject/analysis:v1.0 .

# Test locally (on macOS with XQuartz)
xhost + 127.0.0.1
docker run -it \
  -e DISPLAY=host.docker.internal:0 \
  -v /path/to/data:/arc/projects/myproject \
  myproject/analysis:v1.0
```

---

## 📦 Publishing to Registry

### 1. Access Registry
Visit [images.canfar.net](https://images.canfar.net) and login with your CADC credentials.

### 2. Create Project
- Click "New Project"
- Name: `yourgroup-containers`
- Visibility: Private (initially)
- Add collaborators as needed

### 3. Push Container
```bash
# Login to registry
docker login images.canfar.net
# Here you will use your token copied from the images.canfar.net

# Tag your image
docker tag myproject/analysis:v1.0 \
  images.canfar.net/yourgroup-containers/analysis:v1.0

# Push to registry
docker push images.canfar.net/yourgroup-containers/analysis:v1.0
```

### 4. Test on CANFAR
1. Go to [CANFAR Portal](https://www.canfar.net)
2. Launch → "notebook" # if your container has jupyterlab installed
3. Select your group: `yourgroup-containers`
3. Select your container name: `analysis:v1.0`
4. Test functionality

---

## 🔬 Container Types

### Notebook Containers (`notebook`)
Perfect for data analysis environments:
It must contain the `jupyterlab` executable to be launched as `notebook` kind (type).
Many existing public containers already have what you need. Ex:

```dockerfile
FROM jupyter/scipy-notebook:latest

# Install additional OS packages
USER root
RUN apt-get update && apt-get install -y swarp

# Install additional Python packages
USER jovyan
RUN pip install --no-cache-dir \
    your-package==1.2.3 \
    another-package>=2.0

```

### Desktop Applications (`desktop-app`)
Useful for desktop GUI-based software which does not have a browser-native alternative
If a container is labelled as `desktop-app`, it will expect a startup file. If no `/skaha/startup.sh` file is provided in the container, it will attempt to launch the container with `xterm`. That also means you can turn any existing container into a `desktop-app` container if you have `xterm` installed in your container.

Example with a container capable of running swarp from a desktop xterm:

```dockerfile
FROM ubuntu:latest

# Install your GUI application
USER root
RUN apt-get update && \
    apt-get install -y xterm swarp \
    && rm -rf /var/lib/apt/lists/*
```
Note you can perfectly run `swarp` with a `headless` container, in which case you don't need to labelled `desktop-app` and do not need to install `xterm` which pulls a list of extra dependencies.


Example with a container capable of running `xeyes`:
- the `startup.sh` script (same directory as the `Dockerfile`)
```bash
#!/bin/bash
xeyes
```

- the `Dockerfile`:
```dockerfile
FROM ubuntu:latest

# Install your GUI application
USER root
RUN apt-get update && \
    apt-get install -y xeyes \
    && rm -rf /var/lib/apt/lists/*

# start up xeyes directly, bypassing the xterm
RUN mkdir /skaha
COPY startup.sh /skaha/startup.sh
RUN chmod +x /skaha/startup.sh
```

### Browser-native Container Applications  (`contributed`)

Some interactive applications have native support to the browser. JupyterLab, CARTA and Firefly are examples of these, which CANFAR provide specific label. User can make their own.
The requirements are:
- the application needs to run on port 5000. (many servers have optional port selections)
- the container needs to have a `/skaha/startup.sh` file which will start the application in foreground

Example:
- The `startup.sh` script:
```bash
my_beautiful_replacement_of_notebook \
  --no-browser \
  --host="0.0.0.0" \
  --port=5000
```

```dockerfile
FROM images.canfar.net/skaha/base:latest

RUN mamba install my_beautiful_replacement_of_notebook

EXPOSE 5000

# start up topcat directly, bypassing the xterm
RUN mkdir /skaha
COPY src/startup.sh /skaha/startup.sh
RUN chmod +x /skaha/startup.sh
```
---

## 🧪 Testing Strategies

### Local Testing
```bash
# Test basic functionality
docker run --rm mycontainer:latest python -c "import mypackage; print('OK')"

# Test with mounted storage
docker run --rm \
  -v /path/to/test/data:/arc/projects/test \
  mycontainer:latest \
  python /opt/scripts/test_analysis.py

# Test interactively "entering" the container
docker run --rm -it \
  -v /path/to/test/data:/arc/projects/test \
  mycontainer:latest \
  bash
```

### CANFAR Testing
1. **Upload test container** to registry
2. **Launch test session** on CANFAR
3. **Verify file access** to `/arc/projects`
4. **Test core functionality**
5. **Check resource usage** (memory, CPU)


---

## 📋 Best Practices

### Performance
- **Use multi-stage builds** to minimize image size
- **Cache dependencies** in separate layers 
- **Pin package versions** for reproducibility
- **Clean up** package managers and temporary files

```dockerfile
# Good: Multi-stage build
FROM images.canfar.net/skaha/astroml:latest AS builder
RUN conda install large-build-dependency

FROM images.canfar.net/skaha/astroml:latest
COPY --from=builder /opt/conda/lib/specific-files /opt/conda/lib/
```

### Security
- **Never include secrets** in containers
- **Use official base images** when possible
- **Regularly update** base images
- **Scan for vulnerabilities**

### Documentation
- **Include README.md** with usage instructions
- **Document required resources** (CPU, memory, storage)
- **Provide example commands** and workflows
- **List known limitations**

---

## 🔄 Container Lifecycle

### Version Management
```bash
# Use semantic versioning
docker tag mycontainer:v1.0.0    # Major release
docker tag mycontainer:v1.0.1    # Bug fix
docker tag mycontainer:v1.1.0    # New features
docker tag mycontainer:v2.0.0    # Breaking changes
```

### Updates and Maintenance
- **Regular base image updates** for security patches
- **Test with new CANFAR platform versions**
- **Monitor container usage** and performance
- **Deprecate old versions** gracefully

---

## 🆘 Getting Help

### Troubleshooting
- **Build failures**: Check Dockerfile syntax and base image compatibility
- **Runtime errors**: Verify user permissions and environment variables
- **Performance issues**: Monitor resource usage and optimize accordingly

### Support Channels
- **Container development**: [GitHub Issues](https://github.com/opencadc/science-containers/issues)
- **Registry questions**: [support@canfar.net](mailto:support@canfar.net)
- **Community help**: [Discord community](https://discord.gg/YOUR_INVITE_LINK)

### Documentation
- **Docker best practices**: [Docker documentation](https://docs.docker.com/develop/dev-best-practices/)
- **CANFAR specifics**: [Complete container guide](../user-guide/containers/index.md)
- **Platform updates**: [Science platform repository](https://github.com/opencadc/science-platform)
