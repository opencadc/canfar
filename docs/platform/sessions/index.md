# Sessions

A Session is a user-owned compute environment launched from a Container Image
on a Science Platform Server. Choose the Session Kind that matches the way you
want to work:

| Kind | Interface | Typical use |
| --- | --- | --- |
| `notebook` | JupyterLab | Python analysis and interactive notebooks |
| `desktop` | Browser desktop | CASA and other graphical applications |
| `carta` | CARTA | Image and spectral-cube exploration |
| `firefly` | Firefly | Tables and image visualization |
| `contributed` | Application-specific | Community-maintained tools |
| `headless` | No interactive interface | Batch commands and pipelines |

See the individual guides for [Notebook](notebook.md), [Desktop](desktop.md),
[CARTA](carta.md), [Firefly](firefly.md), [Contributed](contributed.md), and
[Batch](batch.md) workflows.

## Start a Session

You can launch a Session from the [Science Portal](https://www.canfar.net/),
from the CLI, or with the Python client. The CLI uses a Container Image and
Session Kind as positional arguments:

```bash
canfar login cadc
canfar image ls --kind notebook
canfar create notebook IMAGE_NAME --name analysis
canfar ps --all
```

Use `canfar server ls` and `canfar server use NAME` when more than one Science
Platform Server is available for the active Identity Provider. The image list
is the source of truth for image names and supported kinds; examples are
illustrative tags, not a guarantee that every deployment publishes them.

## Lifecycle and status

Creation returns Session IDs before the Session is necessarily ready. A Session
can be `Pending` while it waits for admission, resources, image pulls, or
initialization, then become `Running` or a terminal state. Queue order and
resource policy are deployment-owned.

```bash
canfar ps --all
canfar info SESSION_ID
canfar events SESSION_ID
canfar logs SESSION_ID
```

The default `canfar ps` view shows `Pending` and `Running` Sessions; use
`--all` to include terminal states as well. `canfar open` only opens a ready
Session. Delete a Session when its work is complete:

```bash
canfar delete SESSION_ID
```

## Storage boundary

Sessions are temporary compute environments. A Session can use mounted
`/arc/home/<user>` and `/arc/projects/<project>` paths when the deployment
provides them, plus `/scratch` for fast Session-local work. `/scratch` is
deleted with the Session. Save scripts, inputs, and results under `/arc` or a
persistent VOSpace Service before stopping or deleting the Session.

For remote VOSpace data, use [canfar data](../storage/transfers.md) or the
explicit Python [storage helper](../storage/filesystem.md). Do not assume that
opening a remote object provides server-side random access; stage once when a
path-oriented tool needs a local filename.

## Resource requests

Omit `--cpu` and `--memory` for the platform's flexible request, or set values
based on measured workload needs. Fixed requests can wait longer when matching
capacity is unavailable. For headless workloads, see the [batch queue and
troubleshooting guide](batch.md).

## Session APIs

The Python client exposes synchronous and asynchronous Session operations. The
public library returns ordinary Python values; it does not replace the mounted
filesystem or add a second storage adapter. Start with the [Python client
guide](../../client/get-started.md) and [Session reference](../../client/session.md).

Some interactive applications expose their own API after the Session reaches
`Running`. Consult the application documentation linked from its individual
guide rather than assuming that every Session has an HTTP API.

## Related guides

- [Storage](../storage/index.md)
- [Containers](../containers/index.md)
- [Permissions](../permissions.md)
- [Support](../support/index.md)
