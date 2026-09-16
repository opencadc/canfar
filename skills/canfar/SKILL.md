---
name: canfar
description: Use the CANFAR Science Platform CLI and Python client to launch astronomy sessions, run replicated batch jobs, inspect results, and access configured VOSpace storage. Use for operating CANFAR or writing scripts that use it.
---

# Work on the CANFAR Science Platform

Help the user complete an astronomy workflow with their installed `canfar`
client. A **Session** is a running application or batch job inside a container
on a **Science Platform Server**. A **Container Image** packages its software.

## Establish the installed interface

Inspect `canfar version`, `canfar --help`, and the relevant command's `--help`
before composing commands. These examples target the interface with leaf
`-o/--output` options and explicit `canfar.storage.filesystem()` access.
Older releases have different flags and Python APIs; a development checkout
can retain an older version number. Check capabilities as well as the version.
Do not upgrade an environment merely to make an example work.

Use the user's existing environment. When installation is requested, use its
package manager (`uv add canfar` for a uv project or `pip install canfar` in a
virtual environment). Confirm the installed release supports the needed
feature. A release from the package index may lag a development branch.

For details, consult the [CANFAR documentation](https://opencadc.github.io/canfar/)
for the installed version. In a checkout, use `docs/cli/cli-help.md`,
`docs/cli/authentication-contexts.md`, `docs/client/data.md`, and
`docs/client/session.md`, checking them against source when they disagree.

## Choose identity, server, and data separately

An **Identity Provider (IDP)** verifies who you are. A saved **Authentication
Record** holds credentials. **Server Selection** chooses where new Session
requests go; it does not move existing Sessions. A **Storage Identifier** names
a configured data service and is separate from that Server Selection.

```bash
canfar auth show
canfar server ls
canfar config get active.server
```

`server ls` can discover and save Servers when none are saved. If login is
needed, use the user's IDP: `canfar login cadc` for CADC certificate login or
`canfar login srcnet` for SRCNet OpenID Connect (OIDC). Let the user complete
credential entry and browser approval. OIDC prints a verification URL and user
code and tries to open a browser; on a remote terminal, the user can open the
printed URL on their own machine. `--timeout` limits HTTP requests, not the
time allowed for browser approval.

For saved identities, `canfar auth use IDP` switches identity and
`canfar server use SELECTOR` selects a Server by name or IVOA resource URI.
Confirm the target before submitting work if multiple Servers are available.
Do not erase configuration to recover from an ordinary login failure.

## Launch and inspect Sessions

Find an available image with `canfar image ls --kind notebook` (or the required
kind). Use an explicit image tag when repeatability matters. Do not assume an
example image, GPU, resource size, or path exists on the chosen Server.

```bash
canfar create notebook IMAGE --name analysis -o json
canfar ps --all -o json
canfar info SESSION_ID
canfar events SESSION_ID
canfar logs SESSION_ID
canfar open SESSION_ID
```

Replace `IMAGE` and `SESSION_ID` with the selected image and returned ID.
`create -o json` returns a list of created IDs; a shorter list means some
replicas were not created. Preserve those IDs for monitoring and cleanup.

`ps` shows Pending and Running Sessions by default. Add `--all` when looking
for completed or failed jobs, including when using `--status`. Creating a
Session does not mean it is ready: inspect its returned ID until it is Running
and has a nonempty `connectURL` before opening it. Use bounded polling and
report timeout or terminal failure; do not launch a duplicate merely because
the first Session is still Pending.

For fixed resources, specify both `--cpu` and `--memory` (GB). Omitting both
uses the Server's flexible resource policy; query the Server rather than
assuming fixed limits. `--replicas N` creates N Sessions with per-Session
resource requests.

Headless Sessions run a command and exit. Put all CANFAR options before `--`:

```bash
canfar create headless IMAGE --name reduction --replicas 4 -o json -- python /arc/projects/PROJECT/reduce.py
```

Every token after `--` belongs to the container command. The script must exist
inside the image or on storage mounted into the Session; a laptop path is not
uploaded by `create`. Save outputs in the user's persistent project space.
Treat `/scratch` as temporary storage that is removed with the Session.

## Write Python workflows

Use `Session` for synchronous scripts and `AsyncSession` inside an async
application. Close them with `with` or `async with`. CLI login saves the
identity and Server Selection these clients use by default.

```python
from canfar.sessions import Session

with Session() as sessions:
    ids = sessions.create(
        name="reduction",
        image="IMAGE",
        kind="headless",
        cmd="python",
        args="/arc/projects/PROJECT/reduce.py",
        replicas=4,
    )
    if not ids:
        raise RuntimeError("No Sessions were created")
    print(ids)
    print(sessions.info(ids))
```

Replace the image and script path before running. `create()` returns
`list[str]`, omits failed HTTP/network attempts, and returns `[]` on total
launch failure. Invalid requests still raise. `info()` and `fetch()` return
lists of dictionaries; `logs()` returns a dictionary keyed by Session ID and
`events()` returns a list of such dictionaries. `verbose=True` on logs/events
uses logging and returns `None`. `connect()` checks readiness once; it does
not wait for startup.

Python `canfar.login()` / `canfar.alogin()` save credentials and discovered
Servers but do not select the active identity or Server. For a complete
selection flow, use the CLI or explicitly select the saved identity with
`canfar.authentication.use(IDP)` and Server with `canfar.server.use(SELECTOR)`.
In an existing event loop use `await canfar.alogin(...)`, not `asyncio.run()`.
Run synchronous selection/discovery in a worker thread in that case, for
example `await asyncio.to_thread(authentication.use, IDP)`,
`await asyncio.to_thread(server.list_servers)`, and
`await asyncio.to_thread(server.use, SELECTOR)` after importing `asyncio` and
`authentication, server` from `canfar`. Server discovery can start its own
event loop, so do not call it directly from a notebook's running loop.
Python OIDC login prints the verification information; it does not open a
browser. Runtime `token` or `certificate` parameters override saved
credentials for a client without persisting them.

Inside replicated jobs, `canfar.helpers.distributed.chunk(items)` assigns
contiguous work and `stripe(items)` assigns every Nth item. Both use the
1-based `REPLICA_ID` and `REPLICA_COUNT` environment variables. Give every
replica the same ordered input list (for example, a shared manifest or sorted
paths), and write separate output names using the replica ID.

## Access data

Use explicit source-qualified CLI paths:

```bash
canfar data ls -lh arc:/home/USER
canfar data cp local:/absolute/input.fits arc:/home/USER/input.fits
canfar data cp arc:/home/USER/result.fits local:/absolute/result.fits
```

`arc` and `vault` are configured storage names in the default CADC setup;
inspect the user's configuration rather than assuming other Servers provide
them. `local` means the machine executing the command. Data commands can see
all configured Storage Identifiers, not only the active Server's storage.
Each remote source uses the credentials of its owning Server's IDP. Inspect
`servers` in the configuration to identify that owner and authenticate it
separately when needed: SRCNet login does not authenticate default CADC `arc`
or `vault`. Python CADC login expects an existing certificate; use CLI CADC
login with the user to acquire one when absent.

Use `canfar data --help` for installed commands. `cp -R` copies a directory.
Recursive `rm` is disabled in this interface. `mv` operates within one source;
cross-source movement requires copy, verification, then separately authorized
removal. Data commands own their stdout and do not support CANFAR `-o` output.

Python separates the identifier from the path:

```python
from canfar.storage import filesystem, identifiers

print(identifiers())
vault = filesystem("vault")
try:
    vault.get_file("/REMOTE/PATH/input.fits", "/LOCAL/PATH/input.fits")
finally:
    vault.close()
```

Replace both paths. The filesystem uses standard fsspec methods. There are no
dynamic `canfar.storage.vault` attributes or identifier-based fsspec protocols.
Partial reads may transfer or stage the entire object; do not promise reduced
network traffic. For libraries requiring a local path, use `get_file()` and
manage that destination's lifetime. Persistent whole-file caching requires an
explicit fsspec cache and local directory; see the data guide for lifecycle
and backend limitations.

## Output, diagnostics, and cleanup

Use `-o json` or `-o yaml` only on supported data-producing commands: `auth`
(the default view), `auth show`, `auth ls`, `server ls`, `create`, `ps`,
`config show`, and `config get`. Put it on the owning command, not the root.
Do not parse human tables or assume `ps -q` is banner-free. `info`, `logs`,
`events`, `image ls`, and `stats` do not expose this output option.

Root logging options go before the command, for example
`canfar --log-level debug ps -o json`. Diagnostics go to stderr. Debug logs
can include response bodies; keep credentials and private data out of shared
reports. `--log-file PATH` is an optional rotating JSON Lines log.

Delete only the Sessions in the user's requested cleanup scope:
`canfar delete SESSION_ID`. `--force` skips its confirmation and is appropriate
when that deletion is already authorized. Python `destroy(ids)` returns a
dictionary of success booleans; check it before reporting success.
`destroy_with(prefix, *, kind=..., status=...)` supports bulk deletion, but
names containing regular-expression characters have regex semantics. Prefer
the known returned IDs for targeted cleanup. Quote regex arguments in the
shell and pass kind/status explicitly when using `canfar prune`.
