# What's New in Skaha

Stay up to date with the latest features, improvements, and changes in Skaha.

## Recent Updates

!!! info "New in v1.7+"

    ### **🔐 Enhanced Authentication System**
    Skaha now features a comprehensive authentication system with support for multiple authentication modes and automatic credential management.

    ```python title="Authentication Examples"
    from skaha.client import SkahaClient
    from pathlib import Path

    # X.509 certificate authentication
    client = SkahaClient(certificate=Path("/path/to/cert.pem"))

    # OIDC token authentication (configured)
    client = SkahaClient()  # Uses auth.mode = "oidc"

    # Bearer token authentication
    from pydantic import SecretStr
    client = SkahaClient(token=SecretStr("your-token"))
    ```

    ### **🚀 Asynchronous Sessions**
    Skaha now supports asynchronous sessions using the `AsyncSession` class while maintaining 1-to-1 compatibility with the `Session` class.

    ```python title="Asynchronous Session Creation"
    from skaha.session import AsyncSession

    asession = AsyncSession()
    response = await asession.create(
        name="test",
        image="images.canfar.net/skaha/base-notebook:latest",
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

    - 📡 Skaha now uses the `httpx` library for making HTTP requests instead of `requests`. This adds asynchronous support and also to circumvent the `requests` dependence on `urllib3` which was causing SSL issues on MacOS. See [this issue](https://github.com/urllib3/urllib3/issues/3020) for more details.
    - 🔑 Skaha now supports multiple authentication methods including X.509 certificates, OIDC tokens, and bearer tokens with automatic SSL context management.
    - 🏎️💨 Added `loglevel` and `concurrency` support to manage the new explosion in functionality!
    - 🔍 Comprehensive debug logging for authentication flow and client creation troubleshooting.

    ### **🧾 Logs to `stdout`**

    The `[Session|AsyncSession].logs` method now prints colored output to `stdout` instead of returning them as a string with `verbose=True` flag.

    ```python title="Session Logs"
    from skaha.session import AsyncSession

    asession = AsyncSession()
    await asession.logs(ids=["some-uuid"], verbose=True)
    ```

    ### **🪰 Firefly Support**
    Skaha now supports launching `firefly` session on the CANFAR Science Platform.

    ```python title="Firefly Session Creation"
    session.create(
        name="firefly",
        image="images.canfar.net/skaha/firefly:latest",
    )
    ```

!!! info "New in v1.4+"

    ### **🔐 Private Images**

    Starting October 2024, to create a session with a private container image from the [CANFAR Harbor Registry](https://images.canfar.net/), you will need to provide your harbor `username` and the `CLI Secret` through a `ContainerRegistry` object.

    ```python title="Private Image Registry Configuration"
    from skaha.models import ContainerRegistry
    from skaha.session import Session

    registry = ContainerRegistry(username="username", secret="sUp3rS3cr3t")
    session = Session(registry=registry)
    ```

    Alternatively, if you have environment variables, `SKAHA_REGISTRY_USERNAME` and `SKAHA_REGISTRY_SECRET`, you can create a `ContainerRegistry` object without providing the `username` and `secret`.

    ```python title="Private Image Registry with Environment Variables"
    from skaha.models import ContainerRegistry

    registry = ContainerRegistry()
    ```

    ### **💣 Destroy Sessions**
    ```python title="Destroying Sessions"
    from skaha.session import Session

    session = Session()
    session.destroy_with(prefix="test", kind="headless", status="Running")
    session.destroy_with(prefix="test", kind="headless", status="Pending")
    ```

## Previous Versions

For a complete history of changes, see the [Changelog](changelog.md).

## Stay Updated

- 📢 [GitHub Releases](https://github.com/shinybrar/skaha/releases)
- 📝 [Changelog](changelog.md)
- 💬 [Discussions](https://github.com/shinybrar/skaha/discussions)
