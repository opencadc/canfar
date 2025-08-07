# Skaha

!!! note "Skaha Overview"

    A lightweight python interface to the CANFAR Science Platform.

!!! example "Session Creation Example"
    ```python title="Python Session Creation"
    from skaha.session import AsyncSession

    session = AsyncSession()
    sessions = await session.create(
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

[Quick Start :material-coffee:](quick-start.md){: .md-button .md-button--primary }
[Go to GitHub :fontawesome-brands-github:](https://github.com/shinybrar/skaha){: .md-button .md-button--primary }
[Changelog :material-vector-polyline-remove:](changelog.md){: .md-button .md-button--primary }
