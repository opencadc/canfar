# Frequently asked questions

## What is the CANFAR Science Platform?

CANFAR provides interactive and unattended computing Sessions for astronomy,
with access to project storage, configured VOSpace Services, and published
Container Images. The available Servers, images, resources, and Storage
Identifiers depend on the deployment and your account.

## How do I get access?

You need a CADC account and access to a Science Platform Server. Request a
[CADC account](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html)
if needed, then ask the platform or project administrator for CANFAR and group
access. See [Getting started](../get-started.md).

## How do I log in and select a server?

```bash
canfar login cadc
canfar server ls
canfar server use SERVER_NAME
canfar config get active.server
```

`canfar auth` manages saved Authentication Records and `canfar server` manages
the active Server. The removed `canfar context` command is not part of the
current CLI.

## Which Session Kind should I use?

- `notebook` for interactive Python and exploratory work;
- `desktop` for a graphical Linux environment;
- `carta` for image and cube visualisation;
- `firefly` for supported browser-based astronomy applications; and
- `headless` for scripts, reductions, and parameter sweeps.

Use `canfar image ls --kind KIND` to see images available for a kind. See
[Sessions](../sessions/index.md).

## What does `Pending` mean?

`Pending` means the platform accepted the request but has not made the Session
ready. Admission, requested resources, image pulling, or initialization can
all occur while a Session is Pending. `canfar create` returns accepted IDs; it
does not wait for `Running`.

```bash
canfar ps --all
canfar info SESSION_ID
canfar events SESSION_ID
canfar stats
```

Do not assume that headless work has priority over interactive work. Queue
policy is deployment-owned. See [batch processing](../sessions/batch.md).

## What does `canfar create` print?

Human mode reports the accepted Session ID. JSON and YAML modes emit the raw
list of returned IDs, suitable for a script:

```bash
canfar create headless IMAGE_NAME --output json -- python run.py
```

Put CLI options before the `--` delimiter; everything after it is the command
given to the container. A partial result contains the IDs accepted by the
platform. An empty result indicates a creation or transport failure, not a
queued Session.

## Where should I put data?

- `/arc/home/<user>/` for personal persistent files;
- `/arc/projects/<project>/` for project files, when that path is available;
- a configured VOSpace Service for persistent remote data; and
- `/scratch` for temporary, high-speed staging only.

Use explicit `IDENTIFIER:/path` operands with `canfar data`. See [Storage](../storage/index.md)
and [Data transfers](../storage/transfers.md).

## How do I use storage from Python?

The public API uses explicit identifiers:

```python
from canfar.storage import filesystem, identifiers

print(identifiers())
remote = filesystem("IDENTIFIER")
try:
    print(remote.ls("/path"))
finally:
    remote.close()
```

`local` is the machine running the Python process. CANFAR does not register a
dynamic `vault://` or `arc://` protocol and there is no `storage.configure()`
call. See [Filesystem and Python tools](../storage/filesystem.md).

## Can I use a GPU or request more resources?

Use the resource options supported by the current `canfar create --help` and
the image's requirements. A larger fixed request can wait longer for matching
capacity. Record the image and resource request with a reproducible workflow.
Ask the platform operator about deployment-specific GPU availability.

## How do I build or publish a Container Image?

Start with [Container Images](../containers/index.md) and the registry
instructions for your project. Use a stable tag or digest and never store
credentials in an image layer. A pushed image is usable only where the target
Science Platform Server can pull it.

## How do I get help?

Run the checks in [Support](index.md), then email
[support@canfar.net](mailto:support@canfar.net) with a Server Name, timestamp,
exact error, and relevant Session diagnostics. Remove tokens, certificates,
passwords, and private data before sharing logs.
