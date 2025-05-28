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
FROM images.canfar.net/skaha/astroconda:latest

# Install additional packages
RUN conda install -c conda-forge your-package

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
Always start from CANFAR-compatible base images:

```dockerfile
# Recommended base images
FROM images.canfar.net/skaha/astroconda:latest    # Python + astronomy
FROM images.canfar.net/skaha/notebook:latest      # Jupyter environment  
FROM images.canfar.net/skaha/desktop:latest       # Full desktop
FROM images.canfar.net/skaha/casa:latest          # CASA + desktop
```

### Required Features
Your container must:
- **Run as non-root user** (UID 1000, GID 1000)
- **Support `/arc` mount point** for storage access
- **Handle DISPLAY environment** for GUI applications
- **Include necessary dependencies** for your software

### Example User Setup
```dockerfile
# Create skaha user (required)
RUN groupadd -g 1000 skaha && \
    useradd -u 1000 -g 1000 -d /home/skaha -ms /bin/bash skaha

# Switch to skaha user
USER skaha
WORKDIR /home/skaha
```

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

### Using CANFAR Build Service
```bash
# Clone your container repository
git clone https://github.com/yourusername/mycontainer.git
cd mycontainer

# Tag and push (triggers automated build)
git tag v1.0
git push origin v1.0
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

# Tag your image
docker tag myproject/analysis:v1.0 \
  images.canfar.net/yourgroup-containers/analysis:v1.0

# Push to registry
docker push images.canfar.net/yourgroup-containers/analysis:v1.0
```

### 4. Test on CANFAR
1. Go to [CANFAR Portal](https://www.canfar.net)
2. Launch → "Contributed"
3. Enter your container name: `yourgroup-containers/analysis:v1.0`
4. Test functionality

---

## 🔬 Container Types

### Notebook Containers
Perfect for data analysis environments:

```dockerfile
FROM images.canfar.net/skaha/notebook:latest

# Install additional Python packages
RUN pip install --no-cache-dir \
    your-package==1.2.3 \
    another-package>=2.0

# Add custom Jupyter extensions
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager

# Copy analysis notebooks
COPY notebooks/ /opt/notebooks/
```

### Desktop Applications
For GUI-based software:

```dockerfile
FROM images.canfar.net/skaha/desktop:latest

# Install your GUI application
USER root
RUN apt-get update && apt-get install -y \
    your-gui-app \
    && rm -rf /var/lib/apt/lists/*

# Create desktop shortcuts
USER skaha
COPY your-app.desktop /home/skaha/Desktop/
```

### Command-Line Tools
For headless processing:

```dockerfile
FROM images.canfar.net/skaha/astroconda:latest

# Install command-line tools
RUN conda install -c conda-forge \
    your-cli-tool \
    processing-library

# Add processing scripts
COPY scripts/ /opt/scripts/
RUN chmod +x /opt/scripts/*

# Set default command
CMD ["/opt/scripts/process.sh"]
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
```

### CANFAR Testing
1. **Upload test container** to registry
2. **Launch test session** on CANFAR
3. **Verify file access** to `/arc/projects`
4. **Test core functionality**
5. **Check resource usage** (memory, CPU)

### Automated Testing
```yaml
# .github/workflows/test.yml
name: Test Container
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build container
      run: docker build -t test-container .
    - name: Test functionality
      run: docker run --rm test-container python -m pytest tests/
```

---

## 📋 Best Practices

### Performance
- **Use multi-stage builds** to minimize image size
- **Cache dependencies** in separate layers
- **Pin package versions** for reproducibility
- **Clean up** package managers and temporary files

```dockerfile
# Good: Multi-stage build
FROM images.canfar.net/skaha/astroconda:latest AS builder
RUN conda install large-build-dependency

FROM images.canfar.net/skaha/astroconda:latest
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
git tag v1.0.0    # Major release
git tag v1.0.1    # Bug fix
git tag v1.1.0    # New features
git tag v2.0.0    # Breaking changes
```

### Updates and Maintenance
- **Regular base image updates** for security patches
- **Test with new CANFAR platform versions**
- **Monitor container usage** and performance
- **Deprecate old versions** gracefully

---

## 📚 Examples and Templates

### Template Repository
Check out the [CANFAR container templates](https://github.com/opencadc/science-containers/tree/main/science-containers/Dockerfiles) for examples:
- **Notebook template**: Basic Jupyter environment
- **Desktop template**: GUI application container  
- **CLI template**: Command-line processing tools

### Community Containers
Browse [published containers](https://images.canfar.net) for inspiration and reusable components.

---

## 🆘 Getting Help

### Troubleshooting
- **Build failures**: Check Dockerfile syntax and base image compatibility
- **Runtime errors**: Verify user permissions and environment variables
- **Performance issues**: Monitor resource usage and optimize accordingly

### Support Channels
- **Container development**: [GitHub Issues](https://github.com/opencadc/science-containers/issues)
- **Registry questions**: [support@canfar.net](mailto:support@canfar.net)
- **Community help**: [Slack channel](https://cadc.slack.com/archives/C01K60U5Q87)

### Documentation
- **Docker best practices**: [Docker documentation](https://docs.docker.com/develop/dev-best-practices/)
- **CANFAR specifics**: [Complete container guide](../complete/publishing.md)
- **Platform updates**: [Science platform repository](https://github.com/opencadc/science-platform)
