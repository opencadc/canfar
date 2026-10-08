# Install and Set Up

Use the CANFAR Python package to automate work on a Science Platform Server:
launch Sessions, list Container Images, fetch logs, inspect state, and clean up
resources.

## Install

!!! note "Development documentation"

    The examples in this branch describe unreleased changes since v1.4.1.
    The published package does not yet contain every command and Python API
    shown here. Read [What's new](updates.md) and the [upgrade guide](migration.md)
    before changing an existing environment.

### Use the published release

Install the released package for regular use, and use the documentation that
matches that release:

```bash
pip install --upgrade canfar
```

With `uv`:

```bash
uv add canfar
```

### Install on an Intel Mac

`cryptography` 49.0.0 and later publish no Intel macOS wheels, so a plain
install on an Intel Mac tries to compile it and fails with
`Failed to build cryptography`. Install canfar as a [uv](https://docs.astral.sh/uv/)
tool from wheels only. You get `cryptography` 48.0.1, the last Intel release,
in an environment of its own, without Homebrew or a compiler:

```bash
uv tool install canfar --no-build-package cryptography
```

uv remembers the option, so later upgrades need no extra flags:

```bash
uv tool upgrade canfar
```

Do not run `uv run pip install …`: uv-managed Python rejects it with
`error: externally-managed-environment`.

!!! warning "cryptography 48.0.1 has known vulnerabilities"

    | Advisory | Severity | Fixed in |
    | --- | --- | --- |
    | [GHSA-g6cj-pr64-35w5](https://github.com/advisories/GHSA-g6cj-pr64-35w5): PKCS#7 decryption oracle | High | 50.0.0 |
    | [GHSA-jwv3-5hgf-82ww](https://github.com/advisories/GHSA-jwv3-5hgf-82ww): X.509 path-building denial of service | High | 49.0.0 |
    | [GHSA-m2h6-j472-rp4c](https://github.com/advisories/GHSA-m2h6-j472-rp4c): X.509 name-constraint bypass | Moderate | 49.0.0 |

    canfar uses neither PKCS#7 nor X.509 path verification, and no unrelated
    packages share the tool environment.

If `sysctl -n machdep.cpu.brand_string` prints `Apple M…`, your Mac is Apple
Silicon running an Intel Python under Rosetta. Use a native Python instead; it
gets current releases.

### Try this development branch

To test the development examples on `main`, use a separate checkout and Python
environment. With Git and `uv` installed, run:

```bash
git clone --branch main https://github.com/opencadc/canfar.git canfar-preview
cd canfar-preview
uv sync
source .venv/bin/activate
canfar --help
canfar ps --help
```

The activation command above is for a macOS or Linux shell. In another shell,
use `uv run canfar …` from the checkout instead. The checkout still reports
version `1.4.1`; confirm that `canfar ps --help` offers `-o/--output` and that
`canfar data --help` works before following these examples.

The Python environment is separate, but the client still uses your normal
`~/.canfar/config.yaml`. Review the [migration guide](migration.md) before
changing saved configuration.

<span id="log-in"></span>

## Authenticate

The simplest path is to authenticate with the CLI. Python then uses the saved
Authentication Record and Server Selection:

```bash
canfar login cadc
```

Use `canfar login srcnet` if your account belongs to an SRCNet identity provider
(IDP), the service that manages your login. It uses OpenID Connect (OIDC)
device authorization: follow the displayed link to approve the login.

<span id="use-async-workflows"></span>

### Log in directly from Python

The following alternatives perform the same OpenID Connect (OIDC) device
login. Open the displayed verification URL and enter the user-facing code
when prompted by your identity provider.

=== "Sync Python"

    ```python title="login.py"
    import canfar

    canfar.login("srcnet")
    ```

=== "Async Python"

    ```python title="login.py" hl_lines="5"
    import asyncio
    import canfar

    async def main() -> None:
        await canfar.alogin("srcnet")

    if __name__ == "__main__":
        asyncio.run(main())
    ```

In Jupyter, define `main()` without the script entrypoint and run
`await main()` in another cell. The async login performs native asynchronous
network requests.

Python prints the verification URL and user-facing device code, then waits
for approval. It does not open a browser or render the CLI's QR code.
The private OAuth device token is never printed.

Both functions save the Authentication Record and discovered Science Platform
Servers but do not change the active Authentication or Server Selection. They
return `None`; an unknown Identity Provider raises `KeyError`, and credential or
discovery failures raise `canfar.authentication.AuthenticationError`.

### Select the identity and server in Python

After either Python login function completes, select the saved identity and
list its compatible servers:

```python
from canfar import authentication, server

authentication.use("srcnet")
for candidate in server.list_servers():
    print(candidate.name, candidate.url)
```

Choose a name from that output, replace `SERVER_NAME` below, and select it
before you construct a Session client:

```python
server.use("SERVER_NAME")
```

These selection functions are synchronous and save the defaults used by new
clients. In a notebook or another running event loop, run selection and
discovery in a worker thread because they can start their own event loop:

```python
import asyncio
import canfar
from canfar import authentication, server

await canfar.alogin("srcnet")
await asyncio.to_thread(authentication.use, "srcnet")
candidates = await asyncio.to_thread(server.list_servers)
for candidate in candidates:
    print(candidate.name, candidate.url)
```

After choosing a name from that output, run this in the next notebook cell:

```python
await asyncio.to_thread(server.use, "SERVER_NAME")
```

The CLI `canfar login` flow includes selection, so you can use that route instead.

!!! note "Storage and compute can use different accounts"

    The default `arc` and `vault` services use your saved CADC Authentication
    Record, even when compute uses SRCNet. Run `canfar login cadc` for those
    services. Then select SRCNet again for compute with `canfar auth use srcnet`
    and `canfar server use SERVER_NAME` if needed.

<span id="use-fixed-resources"></span>

## Create a Session

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        kind="notebook",
        image="images.canfar.net/skaha/astroml:latest",
        name="my-analysis",
    )
    print(ids)
```

Choose an image available on your selected server using `canfar image ls
--kind notebook`; the image above is an example. Keep the returned IDs to
inspect and clean up this specific run, as shown in the [Python tutorial](quick-start.md).

`create()` returns `list[str]`. A failed replica is omitted and a total HTTP or
network failure returns `[]`; request validation errors still raise.

## Edit and save Configuration

`Configuration` is the persisted data shape. Its top-level fields are
`version`, `active`, `authentication`, `servers`, `registry`, and `console`.
Authentication Records are keyed by Identity Provider, Science Platform Servers
by Server Name, and `active` stores the selected references. The bound
`config.editor` is the supported editing surface:

```python
from canfar.models.config import Configuration

config = Configuration()
width = config.editor.get("console.width")
config.editor.set("console.width", 132)
config.editor.save()
```

`get()` can return a scalar, mapping, or whole list through a dotted path. List
indices are not supported. `set()` validates before mutating the bound model;
invalid updates leave it unchanged. `save()` persists the validated
Configuration atomically. The editor itself is not part of the serialized
Configuration shape.

## Private Container Images

Pass a `ContainerRegistry` in the Configuration when creating a Session from a
private image:

```python
from canfar.models.config import Configuration
from canfar.models.registry import ContainerRegistry
from canfar.sessions import Session

config = Configuration(
    registry=ContainerRegistry(username="username", secret="CLI_SECRET")
)
with Session(config=config) as session:
    ids = session.create(
        kind="notebook",
        image="images.canfar.net/my-project/private-image:latest",
        name="private-image-test",
    )
```

## Read next

- [Python quickstart](quick-start.md)
- [Examples](examples.md)
- [Data access](data.md)
- [Authentication and Servers](../cli/authentication-contexts.md)
- [Session API](session.md)
