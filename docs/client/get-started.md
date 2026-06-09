# Install and Set Up

Use the CANFAR Python package when you want to automate Science Platform work:
launch Sessions, list Container Images, fetch logs, inspect state, and clean up
resources from Python.

## Install

```bash
pip install canfar --upgrade
```

With `uv`:

```bash
uv add canfar
```

## Log in

Authenticate once from the CLI. Python then uses the active Authentication and
Server selection.

```bash
canfar login cadc
```

For SRCNet:

```bash
canfar login srcnet
```

Force a fresh login when credentials expire or you want to replace saved state:

```bash
canfar login cadc --force
```

Check what Python will use:

```bash
canfar auth show
canfar server ls
```

## Create a Session

```python
from canfar.sessions import Session

session = Session()
ids = session.create(
    kind="notebook",
    image="images.canfar.net/skaha/astroml:latest",
    name="my-analysis",
)
print(ids)
```

Open it in your browser:

```python
session.connect(ids)
```

## Use fixed resources

Omit resources for flexible allocation. Pass `cores`, `ram`, and `gpus` when
you need fixed resources.

```python
ids = session.create(
    kind="headless",
    image="images.canfar.net/skaha/astroml:latest",
    name="batch-job",
    cmd="python",
    args="/arc/projects/demo/run.py",
    cores=4,
    ram=16,
)
```

## Use async workflows

```python
from canfar.sessions import AsyncSession

async with AsyncSession() as session:
    ids = await session.create(
        kind="notebook",
        image="images.canfar.net/skaha/astroml:latest",
        name="async-analysis",
    )
    await session.connect(ids)
```

## Private Container Images

Configure Container Registry credentials when you need private images.

```python
from canfar.models.config import Configuration
from canfar.models.registry import ContainerRegistry
from canfar.sessions import Session

config = Configuration(
    registry=ContainerRegistry(username="username", secret="CLI_SECRET")
)
session = Session(config=config)

ids = session.create(
    kind="notebook",
    image="images.canfar.net/my-project/private-image:latest",
    name="private-image-test",
)
```

## Read next

- [Python quickstart](quick-start.md)
- [Examples](examples.md)
- [Authentication and Servers](../cli/authentication-contexts.md)
- [Session API](session.md)
