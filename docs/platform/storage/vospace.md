# VOSpace Services

VOSpace lets you store and transfer astronomical files remotely. Its
[protocol](https://www.ivoa.net/documents/VOSpace/) is defined by the
International Virtual Observatory Alliance (IVOA). A CANFAR Science Platform Server can expose one or
more VOSpace Services. Each service has a user-facing **Storage Identifier** in
the CANFAR configuration and an endpoint discovered from the platform.

VOSpace is remote object storage, not a promise that every deployment behaves
like a mounted POSIX filesystem. Use a mounted `/arc` path inside a Session when
the data is already there; use a VOSpace Service for authenticated remote reads,
writes, sharing, and transfer between machines.

## Choose an access path

| Need | Recommended path |
| --- | --- |
| Upload or download files in your browser | [Storage Management](transfers.md#transfer-files-in-your-browser) |
| Work with data already mounted in a Session | `/arc/home/<user>` or `/arc/projects/<project>` |
| Copy one object or directory from a remote service | `canfar data cp` |
| List or inspect a remote service from a shell | `canfar data ls`, `info`, `stat`, or `find` |
| Use a remote object from Python | `filesystem(identifier)` from `canfar.storage` |
| Feed a path-only program such as CASA | Stage with `get_file()` or `canfar data cp` to `/scratch` |
| Reuse an input during one Session | An explicit `SimpleCacheFileSystem` under `/scratch` |

## CLI access

The embedded data command maps every configured VOSpace Service and the reserved
`local` filesystem for each invocation:

```bash
canfar data ls -lh vault:/project
canfar data cp vault:/project/input.fits local:/scratch/input.fits
canfar data cp local:/scratch/result.fits arc:/projects/<project>/result.fits
```

The `vault:` and `arc:` names are examples, not universal protocol names. Use
the Storage Identifiers configured for the active installation. See [Data
transfers](transfers.md) for copy, directory, removal, and troubleshooting
guidance.

## Python access

The public Python surface is deliberately small:

```python
from canfar.storage import filesystem, identifiers

print(identifiers())
remote = filesystem("vault")
try:
    remote.get_file("/project/catalog.fits", "/scratch/catalog.fits")
finally:
    remote.close()
```

CANFAR resolves the Storage Identifier to its service endpoint and parent
Identity Provider, materializes the saved Authentication Record, and returns a
normal fsspec filesystem. There is no public `storage.configure()`, dynamic
`from canfar.storage import vault` attribute, or runtime `vault://`/`arc://`
registration. The private source factories used by `canfar data` are not part of
the Python API.

## Files, ranges, and staging

`vosfs` exposes standard fsspec methods. Explicit `cat_file(path, start, end)`
and `cat_ranges(...)` may use server-side byte ranges when the negotiated data
endpoint returns a valid `206` response. If the backend returns a complete
response, `vosfs` falls back to a whole-object read and slices it. This preserves
correctness but not range efficiency.

An `open(path, "rb")` handle is a seekable staged file. It transfers the complete
object before a scientific library reads it. Do not infer range efficiency from
the fact that Astropy, NumPy, pandas, h5py, or Xarray accepts a file-like object.
For random access or memory mapping, stage once to `/scratch` and pass the local
path to the library. For chunked Zarr data, use the fsspec mapper and choose
chunks that suit the service; a block cache does not add ranges to a staged
file object.

Measured CADC behaviour is deployment-specific: Vault/minoc accepted validated
ranges, while ARC/Cavern returned whole objects. A federated or custom Storage
Identifier can differ. The stable contract is response-driven fallback, not a
guarantee based on the identifier name.

## Lifetime and permissions

VOSpace retention, quotas, sharing, and permissions are service and project
policies. Confirm the destination and access rights before a large transfer.
Store reproducible results in `/arc` or a persistent VOSpace location, not in
`/scratch`. A cache under `/scratch` is ephemeral; a cache under `/arc` is a
separate local copy whose freshness and cleanup are your responsibility.

Close the Python filesystem when the workflow is finished. Do not keep a
filesystem or open handle alive across a Session shutdown or pass an open
filesystem into a worker process; reconstruct it in the worker with the same
Storage Identifier and usable credentials.

## Related guides

- [Storage overview](index.md)
- [Filesystem and Python tools](filesystem.md)
- [Data transfers](transfers.md)
- [Permissions](../permissions.md)
