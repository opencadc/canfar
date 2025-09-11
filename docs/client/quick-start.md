# 5-Minute Quick Start (Python Client)

!!! success "Goal"
    By the end of this guide, you'll authenticate, launch a compute Session on CANFAR programmatically, inspect it, read logs/events, and clean it up — all from Python.

!!! tip "Prerequisites"
    - CADC Account — [Sign up](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html)
    - You have logged in at least once to the [CANFAR Science Platform](https://canfar.net) and the [Harbor Container Registry](https://images.canfar.net)
    - Python 3.10+

## Installation

<!-- termynal -->
```
> pip install canfar --upgrade
---> 100%
Installed
```

## Authentication

The Python client automatically uses your active authentication context created by the CLI.

```bash title="Login to CANFAR Science Platform"
canfar auth login
```

!!! note "Login Pathways"
    - If you already have a valid CADC X509 certificate at `~/.ssl/cadcproxy.pem`, the CLI will reuse it automatically.
    - If you're an SRCnet user, you'll be guided through an OIDC device flow in your browser.

```bash title="Force Re-Login (optional)"
canfar auth login --force
```

!!! success "What just happened?"
    - The CLI discovered available CANFAR/SRCnet servers
    - You authenticated and obtained a certificate/token
    - The active context was saved for the Python client to use

## Your First Notebook Session

Launch a Jupyter notebook session programmatically.

=== "Notebook Session"

    ```python
    from canfar.sessions import Session

    session = Session()
    session_ids = session.create(
        name="my-first-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
        cores=2,
        ram=4,
    )
    print(session_ids)  # e.g., ["d1tsqexh"]
    ```

=== "`async`"

    ```python
    from canfar.sessions import AsyncSession

    session = AsyncSession()
    ids = await session.create(
        name="my-first-notebook",
        image="images.canfar.net/skaha/astroml:latest",
        kind="notebook",
        cores=2,
        ram=4,
    )
    print(ids)  # e.g., ["d1tsqexh"]
    ```

!!! success "What just happened?"
    - We connected to CANFAR using your active auth context
    - A notebook container was requested with 2 CPU cores and 4 GB RAM
    - The API returned the newly created session ID(s)

### Get Connection URL

Fetch details and extract the connect URL to open your notebook.

=== "Connect to Session"

    ```python
    session.connect(ids)
    ```

=== "`async`"

    ```python
    await session.connect(ids)
    ```

## Peek Under the Hood

When a session is created, it goes through a series of steps to be fully deployed. You can inspect the events to understand the progress, or capture them for monitoring.

=== "Deployment Events"

    ```python
    session.events(ids, verbose=True)
    ```

=== "`async`"

    ```python
    await session.events(ids, verbose=True)
    ```

At any point, you can also inspect the logs from the session. This is especially useful when launching long-running batch jobs.

=== "Session Logs"

    ```python
    session.logs(ids, verbose=True)
    ```

=== "`async`"

    ```python
    await session.logs(ids, verbose=True)
    ```

## Clean Up

When you're done, delete your session(s) to free resources for other users. :simple-happycow:

=== "Destroy Session(s)"

    ```python
    session.destroy(ids)
    ```

=== "`async`"

    ```python
    await session.destroy(ids)
    ```

## Troubleshooting

- Session won't start?

 
    ```python title="Check available resources"
    session.stats()
    ```
    ```python title="Check events/logs"
    session.events(ids, verbose=True)
    session.logs(ids, verbose=True)
    ```
    ```python title="Try smaller resources or different image"
    session.create(..., cores=1, ram=2, image="images.canfar.net/skaha/astroml:latest")
    ```

- Authentication issues?

    ```bash title="Force re-authentication"
    canfar auth login --force --debug
    ```