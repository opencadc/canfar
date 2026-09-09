# Data Access

Read and write files on CANFAR remote storage from Python using
[fsspec](https://filesystem-spec.readthedocs.io/), a common filesystem interface. A
**Storage Identifier** names one VOSpace Service; a path is the path inside that
service. `canfar` does not register Storage Identifiers as fsspec protocols,
module attributes, or dynamic schemes.

## Find and open a Storage Identifier

[Install the client](get-started.md#install) and authenticate first. The default
`arc` and `vault` services use Canadian Astronomy Data Centre (CADC) credentials:
run `canfar login cadc` even if you use SRCNet for compute. Storage uses the
identity provider of its owning server independently of your active selection.

Call `identifiers()` to list available names, then pass one to `filesystem()`:

```python
from canfar.storage import filesystem, identifiers

available = identifiers()          # e.g. ["arc", "vault", "local"]

vault = filesystem("vault")
try:
    path = "/ALMA/test-data/cutouts/test-4d-cube-cutout.fits"
    print(vault.info(path)["size"])
    raw = vault.cat_file(path)
finally:
    vault.close()
```

The `local` identifier is always available and does not require a credential.
Every other identifier must be present in the saved Configuration. The returned
object is a normal synchronous fsspec filesystem; use its standard methods
rather than a CANFAR-specific wrapper.

`filesystem()` accepts runtime credentials when a caller must override saved
state. A non-empty `token` takes precedence over a saved Authentication Record;
`certificate` supplies a runtime X.509 certificate. Runtime credentials are
used only for that filesystem and do not rewrite the saved Configuration.

```python
from canfar.storage import filesystem

vault = filesystem("vault", token="runtime-bearer-token")
try:
    # use vault here
    ...
finally:
    vault.close()

archive = filesystem("arc", certificate="/path/to/cadcproxy.pem")
try:
    # use archive here
    ...
finally:
    archive.close()
```

An unknown Storage Identifier raises `KeyError`. If a saved credential is
missing, expired, invalid, or cannot be materialized, `filesystem()` raises
`AuthContextError` with a login hint; credential contents are not included in
the error.

## Standard fsspec operations

Storage operations use the ordinary fsspec vocabulary:

```python
from canfar.storage import filesystem

vault = filesystem("vault")
try:
    directory = "/ALMA/test-data/cutouts"
    target = f"{directory}/test-4d-cube-cutout.fits"

    names = vault.ls(directory, detail=False)
    metadata = vault.info(target)
    assert vault.exists(target)
    matches = vault.glob(f"{directory}/*cutout.fits")
    all_names = vault.find(directory)

    whole = vault.cat_file(target)
    header = vault.cat_file(target, 0, 2880)
    ranges = vault.cat_ranges([target, target], [0, 100], [80, 180])

    with vault.open(target, "rb") as handle:
        first_bytes = handle.read(80)
finally:
    vault.close()
```

`cat_file(path, start, end)` returns the requested slice. Whether the VOSpace
Service transfers only that slice or downloads the object and slices it locally
depends on the service and its deployed data endpoint. `open()` provides a
seekable file-like object and may stage the complete object locally. Do not
assume that a partial read reduces network traffic.

VOSpace writes use the corresponding fsspec methods (`put_file`, `pipe_file`,
`mkdir`, and `rm`) when the authenticated account has permission:

```python
vault = filesystem("vault")
try:
    vault.pipe_file("/tmp/example.txt", b"hello CANFAR\n")
    vault.rm("/tmp/example.txt")
finally:
    vault.close()
```

Directory listings use an in-memory fsspec listing cache for the lifetime of
the filesystem. Create a new filesystem when another writer's changes must be
observed.

## Materialize a local file

Libraries that require a pathname can use the standard fsspec `get_file()`
operation. The destination is explicit and its cleanup is the caller's
responsibility:

```python
from canfar.storage import filesystem

vault = filesystem("vault")
try:
    vault.get_file(
        "/ALMA/test-data/cutouts/test-4d-cube-cutout.fits",
        "/scratch/cutout.fits",
    )
finally:
    vault.close()
```

For example, a local path can then be opened by a memory-mapping library:

```python
from astropy.io import fits

with fits.open("/scratch/cutout.fits", memmap=True) as hdul:
    data = hdul[0].data
```

## Content caching

`canfar.storage.filesystem()` does not configure a persistent content cache.
The `/scratch` volume on a Science Platform Server Session is useful for
ephemeral staging, but it is not selected implicitly and is cleared with the
Session. If a workflow needs whole-file caching, compose one standard fsspec
cache wrapper and choose its directory explicitly:

```python
from fsspec.implementations.cached import SimpleCacheFileSystem

from canfar.storage import filesystem

remote = filesystem("vault")
try:
    cached = SimpleCacheFileSystem(
        fs=remote,
        cache_storage="/scratch/canfar-vault",
    )
    cached.cat_file("/ALMA/test-data/cutouts/test-4d-cube-cutout.fits")
finally:
    remote.close()
```

One whole-file cache layer is the supported simple choice. Do not stack cache
wrappers, pass a URL as `cache_storage`, or advertise `blockcache`: the staged
VOSpace file object does not provide the fsspec block-cache interface. The
cache wrapper forwards `close()` only when its wrapped filesystem provides it,
so close the known VOSpace client (`remote`) explicitly.

## Python API boundary

The public Python storage surface is deliberately small:

```python
from canfar.storage import filesystem, identifiers
```

The fsspec-cli source mapping is private. There is no configuration helper,
automatic `vos://` scheme, or module member for each configured identifier.
Keep the Storage Identifier and the path as separate arguments.
