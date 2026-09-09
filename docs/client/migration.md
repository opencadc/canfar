# Upgrade the CANFAR client

## Upgrade from v1.4.1

The changes below are **unreleased** on `feat/interfaces`. They are not all
available in the published v1.4.1 package. Choose an installation using
[Install and set up](get-started.md#install), then check `canfar --help` and the
help for each command you automate. The development checkout still reports
`1.4.1`, so the version string alone cannot identify its interface.

See [What's new](updates.md) for new features and the distinction between main
and this branch. Existing scripts need the following changes.

### Update command lines

| Earlier spelling | Current spelling |
| --- | --- |
| `canfar ps --json` | `canfar ps -o json` |
| `canfar auth show --yaml` | `canfar auth show -o yaml` |
| `canfar authentication …` | `canfar auth …` |
| `canfar run …` or `canfar launch …` | `canfar create …` |
| `canfar del SESSION_ID` | `canfar delete SESSION_ID` |
| `canfar auth login IDP` | Prefer `canfar login IDP`; the former remains a deprecated alias |
| `canfar context …` from older clients | Use `canfar auth` for credentials and `canfar server` for server selection |

The output option belongs to the command, not the root `canfar` invocation.
It is supported on `auth` (including bare `auth`, `show`, and `ls`), `server ls`,
`create`, `ps`, `config show`, and `config get`. Do not add it to every command;
`canfar data` has its own output options. Keep root logging controls before the
command:

```bash
canfar --log-level debug ps --all -o json > sessions.json
```

The file receives only the command payload; logs and errors go to stderr.
If you previously used a command's `--debug` to enable logging, use the root
`--log-level debug` instead. Some commands retain `--debug` for domain-specific
inspection; see [Logging](../cli/logging.md).

### Update Python configuration edits

| Removed method | Replacement |
| --- | --- |
| `config.get_value("console.width")` | `config.editor.get("console.width")` |
| `config.set_value("console.width", 132)` | `config.editor.set("console.width", 132)` |
| `config.save()` | `config.editor.save()` |

```python
from canfar.models.config import Configuration

config = Configuration()
config.editor.set("console.width", 132)
config.editor.save()
```

`set()` validates before changing the model; `save()` writes it atomically.
Use the public `canfar.authentication` and `canfar.server` operations for
credential and server selection, rather than removed Configuration service
methods. See [Install and set up](get-started.md#edit-and-save-configuration).
The stored schema is unchanged by the editor move; a reset is unnecessary if
your existing configuration loads successfully.

### Update storage imports from main checkouts

The storage API was added after v1.4.1. If you used the dynamic imports or
source factories on main, replace `from canfar.storage import vault` with an
explicit filesystem. `canfar.storage.sources()` is no longer public.

```python
from canfar.storage import filesystem, identifiers

print(identifiers())
vault = filesystem("vault")
try:
    vault.get_file("/project/input.fits", "/scratch/input.fits")
finally:
    vault.close()
```

Pass the service path to filesystem methods. `vault` and `arc` are configured
names, not `vault://` or `arc://` fsspec protocols. For CLI paths, use
`vault:/project/input.fits`. See [Data access](data.md).

### Select a server after Python login

Python `canfar.login()` and `canfar.alogin()` save credentials and discover
servers without changing your active selection. Follow them with
`canfar.authentication.use(IDP)`, inspect `canfar.server.list_servers()`, then
call `canfar.server.use(SERVER_NAME)` before constructing `Session()`.
The [setup guide](get-started.md#authenticate) shows the complete sequence.

Default `arc` and `vault` storage uses CADC credentials independently of your
compute selection. Log in to CADC for those services even if your Session
uses an SRCNet server.

## Migrate from the older skaha package

The supported package is `canfar`, published from
[opencadc/canfar](https://github.com/opencadc/canfar). Service endpoints and
historical `X-Skaha-*` request headers remain server contracts.

| Old import | Current import |
| --- | --- |
| `from skaha.session import Session` | `from canfar.sessions import Session` |
| `from skaha.session import AsyncSession` | `from canfar.sessions import AsyncSession` |
| `from skaha.client import SkahaClient` | `from canfar.client import HTTPClient` |

`Session` and `AsyncSession` expose equivalent operations. `create()` returns
`list[str]`, omitting replicas that fail with an HTTP or network error; a total
failure returns `[]`. `fetch()` returns `list[dict[str, str]]`. Pass `kind` and
`status` by keyword in `destroy_with(prefix, *, kind=..., status=...)`.

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        name="migrated-session",
        image="images.canfar.net/skaha/terminal:latest",
    )
    print(ids)
```

Omitting `kind` requests a headless Session. Headless Sessions accept `cmd`,
`args`, and `env`; interactive kinds do not accept those command fields.

### Rename runtime environment variables

Replace the old `SKAHA_` prefix in shell profiles, notebooks, and job scripts.
These current variables configure `HTTPClient` and its Session clients:

| Old variable | Current variable | Meaning |
| --- | --- | --- |
| `SKAHA_TOKEN` | `CANFAR_TOKEN` | Runtime bearer token |
| `SKAHA_CERTIFICATE` | `CANFAR_CERTIFICATE` | Path to an X.509 certificate |
| `SKAHA_URL` | `CANFAR_URL` | Service URL; required with a runtime token or certificate |
| `SKAHA_TIMEOUT` | `CANFAR_TIMEOUT` | HTTP timeout in seconds (1–300); not a total workflow deadline |
| `SKAHA_CONCURRENCY` | `CANFAR_CONCURRENCY` | Maximum asynchronous connections (1–128) |

Explicit constructor arguments override these environment values. Runtime
authentication takes precedence over saved credentials for that client;
when both are supplied, a token takes precedence over a certificate.
`CANFAR_LOGLEVEL` separately controls the default CLI logging level. See
[HTTPClient](client.md) and [Logging](../cli/logging.md) for details.

## Recover a legacy configuration

The default configuration path changed from `~/.skaha/config.yaml` to
`~/.canfar/config.yaml`. The current file stores credentials under
`authentication`, servers under `servers`, and selected references under
`active`. Unsupported formats are rejected; the client does not automatically
back up or rewrite them. Running login again cannot bypass an unreadable file.

If the error says a configuration reset is needed:

1. Note the exact configuration file path in the error. Preserve that file;
   it may contain registry settings or server details you need later.
2. Move **only that file** to an unused backup name. For the default path, the
   following example asks before overwriting an existing backup:

    ```bash
    mv -i ~/.canfar/config.yaml ~/.canfar/config.yaml.before-upgrade
    ```

    If that backup already exists, choose another name. Do not delete the
    entire `.canfar`, `.skaha`, or `.ssl` directory. Keep credential backups
    private and do not attach them to bug reports.
3. After confirming the original file has moved, create a fresh configuration:

    ```bash
    canfar login cadc
    canfar auth show
    canfar server ls
    ```

4. Select the intended server with `canfar server use SERVER_NAME`. Reapply
   needed registry or display settings through `canfar config set` or the
   Python editor. Keep the old file until you have verified the new setup.

Use the path in the error instead of the default example if they differ. If
only a particular setting is invalid, correct that setting before considering
a reset. Contact [support](../platform/support/index.md) if the error persists.
