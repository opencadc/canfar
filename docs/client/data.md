# Data Access

Read and write CANFAR VOSpace Services from Python. `canfar` resolves the
endpoints and credentials; [`vosfs`](https://github.com/shinybrar/vosfs) is the
[fsspec](https://filesystem-spec.readthedocs.io/) filesystem that talks to them,
so every tool that already speaks fsspec — astropy, pandas, dask, zarr — works
without an adapter.

Storage lookup is explicit. `canfar` does not register configured names as
fsspec protocols and does not turn them into module attributes. This keeps
fsspec's built-in `local` protocol untouched and makes filesystem ownership and
cleanup visible to the caller.

## Open a VOSpace Service

Run `canfar login` first; the credential resolution is the same one the CLI
uses. To see which Storage Identifiers are available:

```python
from canfar.storage import identifiers

identifiers()      # ['arc', 'vault', 'local']
```

Build one explicitly — including the reserved local filesystem, overriding a
credential, or naming an identifier held in a variable — with `filesystem`:

```python
from canfar.storage import filesystem

vault = filesystem("vault")
staging = filesystem("vault", token="...")        # runtime bearer token
archive = filesystem("arc", certificate="/path/to/proxy.pem")
local = filesystem("local")
```

`filesystem(identifier)` returns the ordinary upstream fsspec object. Close a
remote filesystem when the operation is complete; `local` needs no credential.

## Filesystem operations

The object is a standard fsspec filesystem, so the usual verbs apply:

```python
cutouts = "/ALMA/test-data/cutouts"
target = f"{cutouts}/test-4d-cube-cutout.fits"

vault.ls(cutouts, detail=False)      # ['/ALMA/.../test-4d-cube-cutout.fits', ...]
vault.info(target)["size"]           # 169920
vault.exists(target)                 # True
vault.isdir(cutouts)                 # True
vault.glob(f"{cutouts}/*cutout.fits")
vault.find(cutouts)                  # recursive listing
vault.du(cutouts)                    # 3712320
```

Reads come in whole-object, ranged, and file-like forms:

```python
whole = vault.cat_file(target)                       # 169920 bytes
header = vault.cat_file(target, 0, 2880)             # first 2880 bytes only
first, second = vault.cat_ranges([target, target], [0, 100], [80, 180])

with vault.open(target, "rb") as handle:
    handle.read(80)

vault.head(target, 100)
vault.tail(target, 100)
```

Writes use `put_file`, `pipe_file`, `mkdir`, and `rm`. Directory listings are
cached in memory for the lifetime of the filesystem object, so a long-lived
object can serve a stale listing; build a fresh filesystem when you need to
observe another writer's changes.

## Get a local path

Some libraries want a real path rather than a file object — anything that
memory-maps, or a C extension that opens by name. Materialise the file:

```python
vault.get_file(target, "/scratch/cutout.fits")
```

`get_file` is the standard fsspec verb; `put_file` is its counterpart for
uploads.

## Cache

`filesystem()` never enables a persistent content cache. Directory-listing
caching is an in-memory fsspec option on the returned object; it is not a byte
cache. If you choose to cache object contents, construct one fsspec cache
wrapper explicitly and own its directory, freshness policy, and cleanup. The
presence of `/scratch` or any `skaha_*` environment variable does not enable
caching.

On a CANFAR Session `/scratch` is fast local NVMe, is not backed up, and is
cleared when the Session ends. It is a useful explicit location for ephemeral
staging or caching, but it is never selected implicitly.

### Whole files

```python
from fsspec.implementations.cached import WholeFileCacheFileSystem

cached = WholeFileCacheFileSystem(fs=vault, cache_storage="/scratch/vault-cache")

cached.cat_file(target)   # cold: fetched over the network
cached.cat_file(target)   # warm: served from /scratch
```

The first read fetches the complete object; subsequent reads can come from the
explicit cache directory.

Use `SimpleCacheFileSystem` when you do not need the expiry and staleness
metadata `WholeFileCacheFileSystem` keeps. Passing `cache_storage` a list of
directories tries each in order and treats only the last as writable, so a
shared read-only cache can back your own.

### Byte ranges

For an explicit partial read, `vosfs` sends an HTTP `Range` request and uses a
validated `206` response. If the byte endpoint returns the whole object with
`200`, `vosfs` falls back to downloading that object and slicing it locally.
Range support is therefore deployment-specific; do not infer it from a
Storage Identifier's spelling or assume that a partial call saves bytes.

```python
header = vault.cat_file(target, 0, 2880)
```

The result is correct in either case. `open()` is a separate path: `vosfs`
stages the complete object into a seekable local file before returning the
file-like object. Use an explicit whole-file cache or `get_file()` when a
scientific tool will read the same object more than once.

### What does not work

`blockcache` (`CachingFileSystem`) cannot wrap a VOSpace Service. Range is
negotiated for explicit byte reads, not through the staged file-object path:

```text
AttributeError: 'StagedReadFile' object has no attribute 'blocksize'
```

Use one explicit cache layer, on a local directory you own; do not silently
stack caches or select one from environment variables.

## Scientific tools

### astropy

Read a header through the explicit byte-read path. Depending on the negotiated
backend, this may transfer only the requested slice or the whole object:

```python
from astropy.io import fits

raw = vault.cat_file(target, 0, 2880)
header = fits.Header.fromstring(raw.decode("latin-1"))
header["NAXIS"], header["OBJECT"]    # 4, 'hers1'
```

Or hand the file object straight to astropy:

```python
with vault.open(target, "rb") as handle, fits.open(handle) as hdul:
    hdul[0].data.shape      # (1, 96, 26, 16)
```

To memory-map, materialise the file first — `memmap=True` needs a real path:

```python
vault.get_file(target, "/scratch/cutout.fits")

with fits.open("/scratch/cutout.fits", memmap=True) as hdul:
    data = hdul[0].data     # paged in on demand, not loaded up front
```

### numpy

```python
import numpy as np

raw = vault.cat_file(target)
values = np.frombuffer(raw[2880:2880 + 64], dtype=">f4")
```

### pandas

Astronomy tables usually arrive as FITS rather than CSV. Read one remotely and
convert:

```python
from astropy.table import Table

with vault.open("/APASS/north/091106/n091106.0101.cat", "rb") as handle:
    table = Table.read(handle, format="fits")

frame = table.to_pandas()    # 2373 rows
frame.columns[:3]            # ['NUMBER', 'MAG_AUTO', 'MAGERR_AUTO']
```

For delimited text, pass the file object to pandas directly:

```python
import pandas as pd

with vault.open("/path/to/table.csv", "rb") as handle:
    frame = pd.read_csv(handle)
```

### dask

Memory-map a materialised cube and chunk it, so only the blocks a computation
touches are paged in:

```python
import dask.array as da
from astropy.io import fits

with fits.open("/scratch/cutout.fits", memmap=True) as hdul:
    array = da.from_array(hdul[0].data, chunks=(1, 24, 26, 16))
    array.mean().compute()
```

## Async

`filesystem(identifier)` intentionally returns the synchronous fsspec object.
The embedded `canfar data` command owns its asynchronous source lifecycle. For
Python scientific tools, use the synchronous object above; it is also the form
that composes with fsspec's content caches and file-like readers.
