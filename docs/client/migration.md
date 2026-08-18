# `skaha` to `canfar`

The supported Python package is now `canfar`, published from
[opencadc/canfar](https://github.com/opencadc/canfar). The service endpoints
and the historical `X-Skaha-*` request headers remain server-side contracts.

## Imports

| Old import | Current import |
| --- | --- |
| `from skaha.session import Session` | `from canfar.sessions import Session` |
| `from skaha.session import AsyncSession` | `from canfar.sessions import AsyncSession` |
| `from skaha.client import SkahaClient` | `from canfar.client import HTTPClient` |

`Session` and `AsyncSession` are separate native clients with equivalent public
operations. `create()` returns `list[str]`; `fetch()` returns
`list[dict[str, str]]`. The filters after `destroy_with(prefix)` are
keyword-only in both clients.

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        name="migrated-job",
        image="images.canfar.net/skaha/terminal:latest",
    )
```

`kind` defaults to `"headless"` when it is omitted. For headless Sessions,
`cmd`, `args`, and `env` remain available; interactive kinds do not accept
headless command fields.

## Configuration

The default file moves from `~/.skaha/config.yaml` to
`~/.canfar/config.yaml`. The current persisted shape separates:

- `authentication`: Authentication Records keyed by Identity Provider;
- `servers`: Science Platform Servers keyed by Server Name; and
- `active.authentication` / `active.server`: the active references.

Use the bound `Configuration.editor` for validated dotted updates and atomic
persistence. Do not call the removed Configuration service methods:

```python
from canfar.models.config import Configuration

config = Configuration()
config.editor.set("console.width", 132)
config.editor.save()
```

See [Install and set up](get-started.md#edit-and-save-configuration) for the
full editor contract.

## Authentication and data

Use `canfar login` or the Python `canfar.login()` / `canfar.alogin()` helpers to
create Authentication Records. Python OIDC login prints the verification URL
and user-facing device code to the terminal; the CLI owns browser, QR, and
progress presentation. See [Install and set up](get-started.md#authenticate).

For VOSpace access, replace implicit or package-specific storage helpers with
explicit Storage Identifiers:

```python
from canfar.storage import filesystem, identifiers

print(identifiers())
with filesystem("vault") as vault:
    data = vault.cat_file("/project/observations/example.fits")
```

Storage Identifiers are not dynamic module members or fsspec schemes. See
[Data Access](data.md) for standard fsspec operations.

## Runtime configuration and logging

The package-level `canfar.configure_logging()` function configures application
logging. `HTTPClient` accepts runtime `token` and `certificate` values, which
take precedence over saved Authentication Records for that client only.

For CLI command names and output, use the [CLI documentation](../cli/cli-help.md)
rather than the Python migration guide.
