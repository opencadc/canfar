# Python Quickstart

This guide creates a notebook Session, inspects it, and deletes it from Python.

## 1. Authenticate

```bash
pip install canfar --upgrade
canfar login cadc
```

Use `canfar login srcnet` for SRCNet.

## 2. Create a notebook

```python
from canfar.sessions import Session

session = Session()
ids = session.create(
    kind="notebook",
    image="images.canfar.net/skaha/astroml:latest",
    name="quickstart-notebook",
    cores=2,
    ram=4,
)
print(ids)
```

`create()` returns a list of Session IDs.

## 3. Open the notebook

```python
session.connect(ids)
```

The notebook can take a minute or two to become reachable. Check status:

```python
running = session.fetch(kind="notebook", status="Running")
print(running)
```

## 4. Inspect events and logs

```python
session.events(ids, verbose=True)
session.logs(ids, verbose=True)
```

## 5. Clean up

```python
session.destroy(ids)
```

## Async version

```python
from canfar.sessions import AsyncSession

async with AsyncSession() as session:
    ids = await session.create(
        kind="notebook",
        image="images.canfar.net/skaha/astroml:latest",
        name="quickstart-notebook",
    )
    await session.connect(ids)
    await session.events(ids, verbose=True)
    await session.destroy(ids)
```

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Authentication fails | Run `canfar --log-level debug login cadc --force`. |
| Session does not start | Run `canfar stats`, then try smaller `cores` or `ram`. |
| Browser URL fails | Wait 60-120 seconds and confirm the Session is `Running`. |
| Script needs stable output | Use CLI machine output such as `canfar ps --json`. |

See [Logging](../cli/logging.md) for the CLI and Python
logging controls.
