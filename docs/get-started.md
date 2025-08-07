# Installation & Setup

This guide covers everything you need to install and configure Skaha for use with Science Platform servers worldwide.

!!! tip "New to Skaha?"
    If you want to jump right in with a hands-on tutorial, check out our [5-Minute Quick Start](quick-start.md) guide first!

## Prerequisites

Before you can use Skaha, you need:

- **Python 3.10+** installed on your system
- **A Science Platform account** - For CANFAR, [request an account with CADC](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html)

## Installation

Install Skaha using `pip`:

```bash
pip install skaha --upgrade
```

!!! tip "Virtual Environments"
    We recommend using a virtual environment to avoid conflicts with other packages:
    ```bash
    python -m venv skaha-env
    source skaha-env/bin/activate  # On Windows: skaha-env\Scripts\activate
    pip install skaha
    ```

## Authentication Setup

Skaha uses an authentication context system to manage connections to multiple Science Platform servers. The easiest way to get started is with the CLI login command.

### Quick Authentication

To authenticate with a Science Platform server:

```bash
skaha auth login
```

This command will:

1. **Discover available servers** worldwide
2. **Guide you through server selection**
3. **Handle the authentication process** (X.509 or OIDC)
4. **Save your credentials** for future use

!!! example "Example Login Flow"
    ```bash
    $ skaha auth login
    Starting Science Platform Login
    Discovery completed in 2.1s (5/18 active)

    Select a Skaha Server:
    » 🟢 CANFAR  CADC
      🟢 Canada  SRCnet
      🟢 UK-CAM  SRCnet

    X509 Certificate Authentication
    Username: your-username
    Password: ***********
    ✓ Login completed successfully!
    ```

### Using Skaha Programmatically

Once authenticated via CLI, you can use Skaha in your Python code:

```python
from skaha.session import Session
from skaha.images import Images

# Uses your active authentication context
session = Session()
images = Images()

# List available images
container_images = images.fetch()
print(f"Found {len(container_images)} container images")

# Create a notebook session
session_info = session.create(
    kind="notebook",
    image="images.canfar.net/skaha/base-notebook:latest",
    name="my-analysis",
    cores=2,
    ram=4
)
print(f"Created session: {session_info.id}")
```

## Private Container Images

To access private container images from registries like CANFAR Harbor, provide registry credentials:

```python
from skaha.models import ContainerRegistry
from skaha.session import Session

# Configure registry access
registry = ContainerRegistry(
    username="your-username",
    password="**************"
)

# Use with session
session = Session(registry=registry)

# Now you can use private images
session_info = session.create(
    kind="notebook",
    image="images.canfar.net/private/my-image:latest",
    cores=1,
    ram=2
)
```

!!! info "Registry Credentials"
    The registry credentials are base64 encoded and passed to the server via the `X-Skaha-Registry-Auth` header.

## Next Steps

Now that you have Skaha installed and configured:

- [x] Try our [5-Minute Quick Start](quick-start.md) for a hands-on introduction to creating and managing sessions.
- [x] Learn about [Authentication Contexts](authentication-contexts.md) for managing multiple servers and advanced authentication scenarios.
- [x] Explore [Basic Examples](examples.md) and [Advanced Examples](advanced-examples.md) for common use cases.
- [x] Check out the [Python API Reference](session.md) for detailed documentation of all available methods.
- [x] Refer to the [FAQ](faq.md) for answers to common questions.

!!! tip "Getting Help"
    - 📖 [Complete CLI Reference](cli-help.md)
    - 💬 [Community Discussions](https://github.com/shinybrar/skaha/discussions)
    - 🐛 [Report Issues](bug-reports.md)
