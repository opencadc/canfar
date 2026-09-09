# Storage

Choose storage by lifetime and by where your code runs. A Science Platform
Session has mounted POSIX storage for working with files and a separate local
scratch volume for temporary work. VOSpace Services provide authenticated
remote access when data is not already mounted.

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
- [Session storage](../sessions/index.md)
- [Permissions](../permissions.md)
