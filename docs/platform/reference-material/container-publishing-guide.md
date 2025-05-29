# 🚀 Container Publishing Guide

Complete guide to building, testing, and publishing custom containers for the CANFAR Science Platform.

## 📋 Container Types Overview

The CANFAR Science Platform supports three types of containers, each designed for specific use cases:

### 🖥️ Session Containers
**Interactive browser-based applications** that run natively in your web browser using HTML5 and WebSocket technologies.

**Examples**: Jupyter notebooks, CARTA image viewer, custom web applications

### 🔧 Software Containers  
**Command-line and batch processing containers** launched with any executable and custom software stacks.

**Examples**: Python analysis scripts, data processing pipelines, automated workflows

### 🏠 Legacy Desktop Applications
**Traditional GUI applications** that require a desktop environment for user interaction.

**Examples**: CASA, Topcat, Aladin, specialized astronomy software

---

## 🏗️ Building Requirements

### Universal Requirements (All Container Types)

All CANFAR containers must meet these basic requirements:

- **Linux x86_64 base**: Built on standard Linux distribution
- **Non-root execution**: Containers run as CADC user, never as root
- **CADC authentication**: Compatible with CADC user identity system

!!! warning "Root Access"
    Root operations must be done during image build phase. If runtime root access is needed, configure sudo for specific actions only.

### 📱 Session Container Requirements

Session containers need specific startup procedures based on type:

| Type | Startup Requirement | Port | Notes |
|------|-------------------|------|-------|
| **notebook** | `jupyter lab` executable | Default | Standard Jupyter Lab startup |
| **carta** | Custom CARTA script | Default | CANFAR-managed initialization |
| **desktop-app** | `xterm` installed | N/A | Desktop managed by infrastructure |
| **contributed** | `/skaha/startup.sh` script | 5000 | Custom web applications |

### 🏠 Legacy Desktop Application Requirements

Desktop applications have additional requirements:

- **Default executable**: Must be `xterm` (ensure it's installed)
- **Desktop integration**: Apps appear in "Applications → Astro Software" menu
- **Harbor labeling**: Must be labeled as `desktop-app` in Harbor registry

---

## ⚙️ Container Initialization

### Initialization Scripts

CANFAR provides two initialization mechanisms for custom setup:

#### `/skaha/init.sh` - Non-blocking Initialization
```bash
#!/bin/bash
# Non-blocking initialization that returns control immediately

# Set up environment variables
export CUSTOM_VAR="value"

# Initialize configuration files
mkdir -p /arc/projects/myproject/.config
cp /opt/defaults/* /arc/projects/myproject/.config/

# Must not block - return control to calling process
exit 0
```

#### `/skaha/startup.sh` - Environment Setup
```bash
#!/bin/bash
# Called with command to execute as parameter

# Set up runtime environment
source /opt/conda/etc/profile.d/conda.sh
conda activate myenv

# Execute the passed command
exec "$@"
```

### 🌐 Contributed Session Containers

For custom web applications, follow these rules:

1. **Traffic**: HTTP requests (including WebSocket) on **port 5000**
2. **Routing**: Requests received at root path (`/`) in container
3. **Browser URLs**: Will be `https://ws-uv.canfar.net/sessions/contrib/<sessionid>`
4. **Startup**: Must provide `/skaha/startup.sh` that accepts sessionid parameter

**Example startup script**:
```bash
#!/bin/bash
# /skaha/startup.sh for contributed session

SESSIONID=$1

# Start your web application
cd /opt/myapp
python app.py --port 5000 --session-id $SESSIONID
```

---

## 📦 Publishing Process

### Step 1: Create Harbor Account

[Harbor](https://goharbor.io/) is CANFAR's container registry for storing and managing container images.

1. Navigate to [images.canfar.net](https://images.canfar.net)
2. Click **"Login with OIDC Provider"**
3. Enter your CADC username and password
4. Set Harbor userid to your CADC username
5. **Request access**: Contact [support@canfar.net](mailto:support@canfar.net) for 'Developer' access to your project

### Step 2: Configure Docker Authentication

1. **Get CLI secret**: 
   - In Harbor: Username → "User Profile" → Copy/set CLI secret
2. **Login to registry**:
   ```bash
   docker login images.canfar.net
   # Username: your-cadc-username  
   # Password: your-cli-secret
   ```

### Step 3: Tag and Push Image

1. **Find your image**:
   ```bash
   docker images
   ```

2. **Tag for Harbor**:
   ```bash
   docker tag <IMAGE_ID> images.canfar.net/<PROJECT>/<IMAGE_NAME>:<VERSION>
   ```

3. **Push to registry**:
   ```bash
   docker push images.canfar.net/<PROJECT>/<IMAGE_NAME>:<VERSION>
   ```

**Example**:
```bash
# Tag and push a Python analysis container
docker tag abc123def456 images.canfar.net/myproject/python-analysis:1.0
docker push images.canfar.net/myproject/python-analysis:1.0
```

### Step 4: Label Container Type

1. Return to [images.canfar.net](https://images.canfar.net)
2. Navigate: Your project → Your image → Select version (tag)
3. **Actions** dropdown → Apply appropriate label:
   - `notebook` - Jupyter Lab containers
   - `desktop-app` - GUI applications
   - `contributed` - Custom web applications
   - No label needed for software/headless containers

---

## 🚀 Launching Containers

### Session Containers (Interactive)

**Portal method**: [www.canfar.net](https://www.canfar.net) → Launch → Select your container

**API method**:
```bash
# Launch session
curl -E <cadcproxy.pem> \
  https://ws-uv.canfar.net/skaha/v0/session \
  -d "name=my-session" \
  -d "image=images.canfar.net/myproject/my-image:1.0" \
  -d "cores=2" \
  -d "ram=4"

# Check session status  
curl -E <cadcproxy.pem> \
  https://ws-uv.canfar.net/skaha/v0/session
```

### Software Containers (Headless)

For batch processing and automated workflows:

```bash
curl -E <cadcproxy.pem> \
  https://ws-uv.canfar.net/skaha/v0/session \
  -d "name=analysis-job" \
  -d "image=images.canfar.net/myproject/analysis:latest" \
  -d "kind=headless" \
  -d "cmd=python" \
  --data-urlencode "args=/opt/scripts/process_data.py input.fits output.fits"
```

**→ [Complete Headless Guide](../headless-execution-guide.md)**

### Desktop Applications

1. **Launch desktop session** from portal
2. **Find your app**: Applications → Astro Software → [Your Project] → [Your App]
3. Apps are organized by Harbor project in the desktop menu

---

## 🧪 Testing Containers

### Session Container Testing

**Local Docker testing**:
```bash
# Test notebook container
docker run -p 8888:8888 your-image:latest

# Test contributed application  
docker run -p 5000:5000 your-image:latest
```

### Desktop Application Testing

- **Local testing**: Limited - Docker cannot provide full GUI display
- **Cloud testing**: Use CANFAR desktop session for complete testing
- **Recommended**: Test GUI functionality in actual CANFAR environment

### Validation Checklist

- [ ] Container starts without errors
- [ ] Required software is accessible
- [ ] Data mounts work correctly (`/arc/projects/`, `/scratch/`)
- [ ] Session type matches intended use case
- [ ] Resource requirements are reasonable

---

## 🔍 Available Resources

### Check Platform Resources
```bash
# View available containers
curl -E <cadcproxy.pem> https://ws-uv.canfar.net/skaha/v0/image

# View resource contexts (CPU/RAM options)
curl -E <cadcproxy.pem> https://ws-uv.canfar.net/skaha/v0/context
```

### Getting Help

- **Technical support**: [support@canfar.net](mailto:support@canfar.net)
- **Development questions**: [CADC Slack](https://cadc.slack.com/archives/C01K60U5Q87)
- **Issues and requests**: [GitHub Issues](https://github.com/opencadc/science-platform/issues)


![CANFAR](https://www.canfar.net/css/images/logo.png){ height="200" }
