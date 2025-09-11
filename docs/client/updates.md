# What's New in CANFAR

Stay up to date with the latest features, improvements, and changes in CANFAR.

!!! success "v1.0"

    :fontawesome-solid-exclamation-triangle: **Breaking Changes**

      - Deprecation of support for Python 3.8 and 3.9.
      - The Python package has been renamed from `skaha` to `canfar`.
      - The `skaha.session` API has been deprecated in favor of `canfar.sessions`.
      - See [Migration guide to migrate from skaha → canfar](migration.md).

    :simple-gnubash: **CLI Support**
    
      - Comprehensive CLI support has been added to the client under the `canfar` entry point. See [CLI Reference](../cli/cli-help.md) for more information.
      - The `canfar` CLI is the recommended way to manage authentication. See [Authentication Contexts](../cli/authentication-contexts.md) for more information.
    
    **🌎 SRCnet Support**
    
      - CANFAR now supports launching sessions on all the SRCnet CANFAR Science Platform instances worldwide.
    
    **:fontawesome-brands-connectdevelop:** OIDC Authentication

      - OpenID Connect (OIDC) authentication is now supported for all SRCnet Science Platform servers where applicable.
    
    **:material-book-outline: Documentation**
    
      - Complete overhaul to bring all documentation sources under a single roof.
      - Significant improvements to the Python client and brand new CLI documentation.

## Recent Updates

!!! info "New in v0.7+"

    ### **🔐 Enhanced Authentication System**
    Canfar now features a comprehensive authentication system with support for multiple authentication modes and automatic credential management.

    ```python title="Authentication Examples"
    from canfar.client import HTTPClient
    from pathlib import Path

    # X.509 certificate authentication
    client = HTTPClient(certificate=Path("/path/to/cert.pem"))

    # OIDC token authentication (configured)
    client = HTTPClient()  # Uses auth.mode = "oidc"

    # Bearer token authentication
    from pydantic import SecretStr
    client = HTTPClient(token=SecretStr("your-token"))
    ```

    ### **🚀 Asynchronous Sessions**
    Canfar now supports asynchronous sessions using the `AsyncSession` class while maintaining 1-to-1 compatibility with the `Session` class.

    ```python title="Asynchronous Session Creation"
    from canfar.session import AsyncSession

    asession = AsyncSession()
    response = await asession.create(
        name="test",
        image="images.canfar.net/skaha/astroml:latest",
        cores=2,
        ram=8,
        gpu=1,
        kind="headless",
        cmd="env",
        env={"KEY": "VALUE"},
        replicas=3,
    )
    ```

    ### **🗄️ Backend Upgrades**

    - 📡 Canfar now uses the `httpx` library for making HTTP requests instead of `requests`. This adds asynchronous support and also to circumvent the `requests` dependence on `urllib3` which was causing SSL issues on MacOS. See [this issue](https://github.com/urllib3/urllib3/issues/3020) for more details.
    - 🔑 Canfar now supports multiple authentication methods including X.509 certificates, OIDC tokens, and bearer tokens with automatic SSL context management.
    - 🏎️💨 Added `loglevel` and `concurrency` support to manage the new explosion in functionality!
    - 🔍 Comprehensive debug logging for authentication flow and client creation troubleshooting.

    ### **🧾 Logs to `stdout`**

    The `[Session|AsyncSession].logs` method now prints colored output to `stdout` instead of returning them as a string with `verbose=True` flag.

    ```python title="Session Logs"
    from canfar.session import AsyncSession

    asession = AsyncSession()
    await asession.logs(ids=["some-uuid"], verbose=True)
    ```

    ### **🪰 Firefly Support**
    Canfar now supports launching `firefly` session on the CANFAR Science Platform.

    ```python title="Firefly Session Creation"
    session.create(
        name="firefly",
        image="images.canfar.net/skaha/firefly:latest",
    )
    ```

!!! info "New in v0.4+"

    ### **🔐 Private Images**

    Starting October 2024, to create a session with a private container image from the [CANFAR Harbor Registry](https://images.canfar.net/), you will need to provide your harbor `username` and the `CLI Secret` through a `ContainerRegistry` object.

    ```python title="Private Image Registry Configuration"
    from canfar.models import ContainerRegistry
    from canfar.session import Session

    registry = ContainerRegistry(username="username", secret="sUp3rS3cr3t")
    session = Session(registry=registry)
    ```

    Alternatively, if you have environment variables, `CANFAR_REGISTRY_USERNAME` and `CANFAR_REGISTRY_SECRET`, you can create a `ContainerRegistry` object without providing the `username` and `secret`.

    ```python title="Private Image Registry with Environment Variables"
    from canfar.models import ContainerRegistry

    registry = ContainerRegistry()
    ```

    ### **💣 Destroy Sessions**
    ```python title="Destroying Sessions"
    from canfar.session import Session

    session = Session()
    session.destroy_with(prefix="test", kind="headless", status="Running")
    session.destroy_with(prefix="test", kind="headless", status="Pending")
    ```

## Previous Versions

For a complete history of changes, see the [Changelog](../changelog.md).

## Stay Updated

- 📢 [GitHub Releases](https://github.com/opencadc/canfar/releases)
- 💬 [Discussions](https://github.com/opencadc/canfar/discussions)
