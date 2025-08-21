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

## Your First Session (Notebook)

Launch a Jupyter notebook session programmatically.

```python title="Create a notebook session"
from canfar.sessions import Session

session = Session()
session_ids = session.create(
    name="my-notebook",
    image="images.canfar.net/skaha/astroml-notebook:latest",
    kind="notebook",
    cores=2,
    ram=4,
)
print(session_ids)  # e.g., ["d1tsqexh"]
```

!!! success "What just happened?"
    - We connected to CANFAR using your active auth context
    - A notebook container was requested with 2 CPU cores and 4 GB RAM
    - The API returned the newly created session ID(s)

### Get Connection URL

Fetch details and extract the connect URL to open your notebook.

```python title="Fetch session info"
from webbrowser import open

info = session.info(session_ids)  # list[dict]
open(info[0]["connectURL"])
```

## Peek Under the Hood

View deployment events to understand startup progress.

```python title="Deployment Events"
session.events(session_ids, verbose=True)
```

Fetch logs (printed with color when verbose=True).

```python title="Session logs"
session.logs(session_ids, verbose=True)
```

## Clean Up

When you're done, delete your session(s) to free resources.

```python title="Destroy session(s)"
session.destroy(session_ids)
# {"d1tsqexh": True}
```

## Async Option (Advanced)

Prefer asyncio? Use the 1:1 compatible `AsyncSession`.

```python title="Asynchronous Sessions"
import asyncio
from canfar.sessions import AsyncSession

async def main():
    asession = AsyncSession()
    sids = await asession.create(
        name="my-notebook",
        image="images.canfar.net/skaha/astroml-notebook:latest",
        kind="notebook",
        cores=2,
        ram=4,
    )
    print(sids)

asyncio.run(main())
```

## Troubleshooting

- Session won't start?
  - Check events/logs: `session.events(ids, verbose=True)`, `session.logs(ids, verbose=True)`
  - Try smaller cores/RAM or a different image
- Auth issues?
  - Re-run: `canfar auth login --force`
  - Ensure `~/.ssl/cadcproxy.pem` exists or OIDC login completed
