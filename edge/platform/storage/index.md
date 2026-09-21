<span id="canfar-storage-systems"></span>

# Storage

Choose storage by lifetime and by where your code runs. A Science Platform
Session has mounted POSIX storage for working with files and a separate local
scratch volume for temporary work. VOSpace Services provide authenticated
remote access when data is not already mounted.

<span id="storage-options-overview"></span>
<span id="storage-in-a-session"></span>
<span id="common-workflows"></span>
<span id="interactive-analysis"></span>
<span id="batch-processing"></span>
<span id="data-sharing-and-collaboration"></span>
<span id="troubleshooting-common-issues"></span>

## Storage at a glance

| Location | Lifetime | Use it for |
| --- | --- | --- |
| `/arc/home/<user>` | Persistent | Personal scripts, configuration, and results |
| `/arc/projects/<project>` | Persistent | Project data and shared results |
| `/scratch` | Session-local; deleted when the Session ends | Staging, intermediate files, and explicitly selected caches |
| A configured VOSpace Service | Service-defined | Remote data and transfers through `canfar data` or fsspec |
| `local` | The machine running the command | Local input and output in `canfar data` and the Python helper |

The exact mounts, quotas, and retention policy belong to the deployment and
your project. Do not treat `/scratch` as a backup. Copy anything you need after
the Session to `/arc` or another persistent destination.

## Checking quotas and requesting more space

In a Session terminal, inspect filesystem capacity and your directory's usage.
Replace `USER` and `PROJECT` with your username and project directory:

```bash title="Terminal inside your Session"
df -h /arc/home/USER /arc/projects/PROJECT
du -sh /arc/projects/PROJECT
```

`df` on any path under `/arc` reports the whole ARC filesystem. It never shows
your home or project allocation, so use it only to confirm the mount.
`du` measures the files you can read and can take time on a large directory.
Usage figures can lag behind a large write or cleanup, so check again after a
few minutes before concluding that nothing changed.

Keep your home directory small: configuration, keys, and short scripts.
Datasets, software environments, and download caches belong in project space.
When home is nearly full, saving files and even logging in to a Session can
fail, so free space there first when either starts to misbehave.
Use the [Vault web interface](https://www.canfar.net/storage/vault/list/)
for Vault data, and ask [support](../support/index.md) to confirm the quota
that applies to your project.

To request more space, email [support@canfar.net](mailto:support@canfar.net)
with your project name, storage location, current usage, requested capacity,
and a short explanation of the research need.

!!! warning "Keep durable results out of /scratch"

    Copy and verify final products under `/arc` or another persistent
    destination before the Session ends. Temporary scratch space is not a backup.

## Use the mounted filesystem first

If data is already under `/arc` in a Science Platform Session, use its normal
POSIX path. This avoids an unnecessary VOSpace request and is the simplest
path for CASA, FITS tools, NumPy, pandas, and other software that expects a
filename.

For data outside the Session, stage one copy into `/scratch` when the workflow
will read it more than once, then write final products to `/arc`:

```text
remote VOSpace Service -> /scratch/input.fits -> analysis -> /arc/projects/<project>/results/
```

## Address a VOSpace Service explicitly

CANFAR calls the configured handle for a VOSpace Service a **Storage
Identifier**. The identifier is configuration data, not a Python module member
or a new fsspec protocol. List identifiers and construct a filesystem explicitly:

```python
from canfar.storage import filesystem, identifiers

print(identifiers())  # configured identifiers, plus the reserved "local"
remote = filesystem("vault")
try:
    entries = remote.ls("/project", detail=False)
finally:
    remote.close()
```

`filesystem("local")` returns a filesystem for the machine where Python is
running. It does not require a CANFAR Authentication Record. A configured
identifier resolves its endpoint and parent Identity Provider through the saved
CANFAR configuration; runtime credentials can be supplied to `filesystem()`
when needed. See [Filesystem and Python tools](filesystem.md).

For shell workflows, use the embedded `canfar data` command application:

```bash
canfar data ls -lh vault:/project
canfar data cp vault:/project/input.fits local:/scratch/input.fits
canfar data cp local:/scratch/result.fits arc:/projects/<project>/result.fits
```

The `local:` operand is always the machine running `canfar`. `vault:` and
`arc:` are examples of Storage Identifiers; use the names returned by your
configuration rather than assuming that every deployment has those identifiers.
See [Data transfers](transfers.md) for command details.

## Concurrent Sessions and shared storage

Every Session you run mounts the same `/arc/home/<user>` and the same project
directories, while each Session gets its own `/scratch`. Two Sessions, or the
replicas of one batch run, can therefore write to the same persistent files at
the same time.

| State | Location | Shared between Sessions? |
| --- | --- | --- |
| Configuration, keys, `~/.canfar` | `/arc/home/<user>` | Yes, all of your Sessions |
| Project data and results | `/arc/projects/<project>` | Yes, all members' Sessions |
| Staging and intermediates | `/scratch` | No, one Session only |

- Give each writer its own output file, named from the input or the replica,
  and keep many writers out of one directory when a run produces thousands of
  files.
- Write to a temporary name and rename it into place, so a reader or a
  restarted job never sees a half-written file.
- Keep SQLite databases and other lock-heavy state on `/scratch` while they are
  active, then copy an export or checkpoint to `/arc`. File locking on a shared
  network filesystem is slow and can corrupt a database opened from two
  Sessions.
- Share with collaborators through `/arc/projects/<project>` or a VOSpace
  Service; another Session cannot see your `/scratch`.

The [advanced batch example](../../client/advanced-examples.md) applies these
rules to a replicated run.

<span id="storage-strategy-and-performance"></span>

## Remote-read performance

`vosfs` and fsspec provide two different read shapes:

- `cat_file(path, start, end)` and `cat_ranges(...)` can request explicit byte
  ranges. The response is validated; a backend that returns a complete `200`
  response is read and sliced correctly, but it still transferred the whole
  object.
- `open(path, "rb")` provides a convenient seekable file object by staging the
  complete object. Passing that handle to Astropy, NumPy, pandas, or h5py does
  not make random access network-efficient.

The capability is deployment-specific. In the measured CADC deployment, the
Vault/minoc service accepts validated `206` responses while ARC/Cavern falls
back to a whole-object response. Do not infer capability from the spelling of a
Storage Identifier. See [Filesystem and Python tools](filesystem.md) for the
backend boundary and scientific-library recipes.

## Related guides

- [Filesystem and Python tools](filesystem.md)
- [Data transfers](transfers.md)
- [VOSpace](vospace.md)
- [CADC archive data](archives.md)
- [Session storage](../sessions/index.md)
- [Permissions](../permissions.md)
