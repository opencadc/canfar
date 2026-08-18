# Filesystem and Python tools

Use a normal `/arc` path inside a Science Platform Session whenever the data is
already mounted. Use `canfar.storage` when Python is running outside the
Session, or when the object lives in a configured VOSpace Service. The module
keeps the CANFAR-owned work—Storage Identifier lookup and Authentication
Record materialization—at one explicit boundary and returns the upstream
fsspec filesystem for everything else.

## Construct a filesystem explicitly

```python
from canfar.storage import filesystem, identifiers

names = identifiers()
print(names)  # configured Storage Identifiers, plus "local"

remote = filesystem("vault")
try:
    print(remote.ls("/project", detail=False))
finally:
    remote.close()
```

`filesystem(identifier)` accepts one configured Storage Identifier. The reserved
identifier `local` returns the local fsspec filesystem and does not use CANFAR
credentials:

```python
from canfar.storage import filesystem

local = filesystem("local")
with local.open("/scratch/result.txt", "w") as handle:
    handle.write("done\n")
```

Configured identifiers are resolved when `filesystem()` is called. Saved
X.509 credentials are validated and saved OIDC records may be refreshed before
the literal credential is handed to `vosfs`. A runtime `token=` or
`certificate=` can be supplied when the application owns the credential:

```python
remote = filesystem("vault", certificate="/path/to/cadcproxy.pem")
try:
    data = remote.cat_file("/project/table.csv")
finally:
    remote.close()
```

The identifier is an argument, not a dynamically imported member. CANFAR does
not register `vault://`, `arc://`, or arbitrary configured names as process-wide
fsspec protocols, and there is no `storage.configure()` call. This keeps
configuration lookup visible and leaves fsspec operations portable to workers.

## Read shape and backend capability

There are two distinct ways to read a remote object:

1. `cat_file(path, start, end)` or `cat_ranges(...)` requests explicit bytes.
   `vosfs` validates a ranged `206` response and falls back to a complete
   response when the service does not provide ranges. A successful call is
   therefore correct on both kinds of backend, but a fallback still transfers
   the whole object.
2. `open(path, "rb")` gives a seekable file-like object backed by a staged local
   copy. It is convenient for libraries, but it is not a network-efficient
   random-access reader: opening it stages the complete object.

The response capability belongs to the deployment, not the name `vault` or
`arc`. The read-only CADC measurements used for this guide saw validated ranges
from Vault/minoc and whole-object fallback from ARC/Cavern. Treat another
deployment or Storage Identifier as unknown until its responses are observed.

For data already mounted at `/arc`, use the path directly. For remote data used
once, a single explicit transfer is often clearer:

```bash
canfar data cp vault:/project/cube.fits local:/scratch/cube.fits
```

## Ephemeral and persistent caches

`filesystem()` does not enable a content cache. The fsspec directory-listing
cache used by the constructed VOSpace filesystem is separate from object-byte
caching. Select one content cache explicitly when repeated reads justify it.

### Session-local cache

`SimpleCacheFileSystem` stores complete objects in the directory you choose.
`/scratch` is a useful default inside a Science Platform Session because it is
local and is deleted with the Session. Key the directory by Storage Identifier
so objects from different endpoints cannot collide:

```python
from fsspec.implementations.cached import SimpleCacheFileSystem

from canfar.storage import filesystem

remote = filesystem("vault")
cached = SimpleCacheFileSystem(
    fs=remote,
    cache_storage="/scratch/canfar-cache/vault",
)
try:
    with cached.open("/project/cube.fits", "rb") as handle:
        process(handle)
finally:
    remote.close()
```

This is opt-in. It does not make a staged file into a ranged reader, and it
does not survive Session deletion. Remove the cache when its data is no longer
needed or when `/scratch` is under pressure.

### Persistent cache

Choose a persistent cache directory only when retaining a local copy across
processes or Sessions is intentional. `WholeFileCacheFileSystem` can check
remote metadata and expire entries; the application owns capacity, freshness,
permissions, and cleanup:

```python
from fsspec.implementations.cached import WholeFileCacheFileSystem

from canfar.storage import filesystem

remote = filesystem("vault")
cached = WholeFileCacheFileSystem(
    fs=remote,
    cache_storage="/arc/home/<user>/.cache/canfar/vault",
    expiry_time=24 * 60 * 60,
    check_files=True,
)
try:
    with cached.open("/project/catalog.csv", "rb") as handle:
        process(handle)
finally:
    remote.close()
```

Do not silently choose `/scratch`, stack cache layers, use a `memory://` cache
location, or recommend `blockcache` for `vosfs` staged file objects. These
choices hide lifetime or capability decisions and can turn every block into a
whole-object transfer.

## Scientific Python recipes

The recipes below use standard library APIs and the filesystem returned by
`canfar.storage`. None of them adds a CANFAR-specific adapter.

### pandas

Pandas accepts a file-like object. A remote `open` stages the complete object;
wrap the filesystem in an explicit `SimpleCacheFileSystem` for repeated reads,
or stage the file once to `/scratch`:

```python
import pandas as pd

from canfar.storage import filesystem

remote = filesystem("vault")
try:
    with remote.open("/project/catalog.csv", "rb") as handle:
        frame = pd.read_csv(handle)
finally:
    remote.close()
```

### NumPy

`numpy.load` accepts a seekable binary handle. Memory mapping requires a real
local filename, so transfer the object to `/scratch` first when using
`mmap_mode`:

```python
import numpy as np

from canfar.storage import filesystem

remote = filesystem("vault")
try:
    with remote.open("/project/array.npy", "rb") as handle:
        array = np.load(handle, allow_pickle=False)
    remote.get_file("/project/array.npy", "/scratch/array.npy")
finally:
    remote.close()

mapped = np.load("/scratch/array.npy", mmap_mode="r", allow_pickle=False)
```

### Astropy FITS

Astropy can consume the staged file-like object directly. For repeated access,
or for a workflow that needs a local path, stage once and use `memmap=True`:

```python
from astropy.io import fits

from canfar.storage import filesystem

remote = filesystem("vault")
try:
    remote.get_file("/project/cube.fits", "/scratch/cube.fits")
finally:
    remote.close()

with fits.open("/scratch/cube.fits", memmap=True) as hdul:
    image = hdul[0].data
```

If a service is known to return a valid range response, an explicit
`cat_file(path, start, end)` can retrieve a small byte slice. Do not infer that
FITS header access through `open()` is ranged; the staged file path downloads
the complete object.

### Dask

For a batch workload in a Science Platform Session, stage input files to
`/scratch` and let Dask read local paths. This avoids asking workers to split a
single staged remote object by byte offset:

```python
import dask.dataframe as dd

frame = dd.read_csv("/scratch/catalog/part-*.csv")
result = frame.groupby("source_id").flux.mean().compute()
```

When workers read remote data directly, construct the filesystem in the worker
environment and ensure every worker has CANFAR/vosfs and usable credentials.
Do not rely on a notebook-only protocol registration or inherit an open
filesystem across a process fork. Dask URL protocols and `storage_options` are
worker-side concerns; explicit construction with `filesystem(identifier)` keeps
the CANFAR endpoint and authentication lookup visible.

### Zarr

Zarr 3 stores chunks as separate objects. Build its documented fsspec mapper
from the explicit filesystem and keep the chunks reasonably large for the
service's metadata and transfer costs:

```python
import dask.array as da
from zarr.storage import FsspecStore

from canfar.storage import filesystem

remote = filesystem("vault")
try:
    store = FsspecStore.from_mapper(remote.get_mapper("/project/cube.zarr"))
    cube = da.from_zarr(store, component="science")
    mean = cube.mean().compute()
finally:
    remote.close()
```

The Zarr, Dask, and fsspec packages must be available in the running
environment. A Zarr chunk is already an object-level read; do not wrap the
whole store in a block cache and assume it creates server-side ranges.

### Other path-oriented tools

For h5py, CASA, or a C/C++ application that opens filenames itself, stage the
object to `/scratch` and pass the local path. This is clearer and safer than
assuming that a path-only consumer can use a VOSpace file-like object.

## Related guides

- [Storage overview](index.md)
- [Data transfers](transfers.md)
- [VOSpace](vospace.md)
- [Python client data access](../../client/data.md)
