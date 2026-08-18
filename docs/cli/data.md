# Data commands

Use `canfar data` to work with configured VOSpace Services and the local
filesystem through the embedded `fsspec-cli` command application.

## Install and authenticate

Data commands are included in the standard installation:

```bash
pip install canfar
canfar login cadc
```

## Address mapped sources

Every operand starts with a Storage Identifier: the handle of a configured
VOSpace Service, or the reserved `local` identifier for the machine where the
command runs. Operands always pair an identifier with an absolute path:

```text
storage-identifier:/absolute/path
local:/absolute/path
```

Every mapped source is available concurrently, regardless of the active Server
Selection. A default CADC login maps two VOSpace Services, `arc` and `vault`,
plus `local`:

```bash
canfar data ls -lh arc:/
canfar data ls -lh arc:/home/[username]
canfar data ls -lh vault:/
```

Use `ls -lh`, or the `ll -h` long-form command, for a human-readable listing.
The `-h` flag reports human-readable sizes and requires a long listing, so
`ls -h` on its own exits with `ls: -h: requires long listing`.

Operands must name a mapped source. Empty `:/path`, bare local paths such as
`/tmp/file`, and `active:/path` are all rejected; there is no `active` alias
and no `canfar storage` command.

## Copy files and directories

Copy one file between local and remote sources:

```bash
canfar data cp local:/absolute/path/file.fits arc:/home/[username]/file.fits
canfar data cp arc:/home/[username]/file.fits local:/absolute/path/file.fits
```

Copy between two VOSpace Services, for example a public test cutout from
`vault` into your `arc` home directory:

```bash
canfar data cp vault:/ALMA/test-data/cutouts/test-4d-cube-cutout.fits arc:/home/[username]/test-4d-cube-cutout.fits
canfar data ls -lh arc:/home/[username]/test-4d-cube-cutout.fits
```

Recursive copy is enabled for admitted local and remote source pairs:

```bash
canfar data cp -R local:/absolute/path/dataset arc:/home/[username]/dataset
```

The tagged upstream implementation builds a bounded manifest, copies files
through host-local staging when sources differ, and verifies destination
metadata. Recursive copy is not atomic and does not create a snapshot; inspect
the destination before removing any source data.

## Move data between sources

Cross-source `mv` is unsupported and exits with status 2:

```text
mv: cross-source move unsupported
```

Move a file between sources explicitly by copying it, verifying the
destination, and only then issuing a separate source removal:

```bash
canfar data cp vault:/folder/file.fits arc:/home/[username]/file.fits
canfar data ls -lh arc:/home/[username]/file.fits
canfar data rm vault:/folder/file.fits
```

Do not use this sequence as a one-command or atomic move.

Recursive removal is disabled by application policy, so `rm` accepts no `-R` or
`-r` flag at all and exits with status 2:

```text
No such option: -R
```

Because recursive directory removal is disabled, directory movement is not a
supported workflow in this release. Any future one-command relocation would be a
separately named, opt-in orchestration feature with stronger destination
verification and residual-state semantics—not portable `mv`.

## Cache data locally

### Directory listings

Each command uses a fresh filesystem with a bounded in-memory directory-listing
cache. The cache is closed with the command and never persists object contents.
It is not controlled by environment variables.

### Files and byte ranges

There is no CLI flag for caching file contents, but `vosfs` is a normal
[fsspec](https://filesystem-spec.readthedocs.io/) filesystem, so an fsspec
cache can wrap the explicit CANFAR Python filesystem. Caching is always a user
choice: `/scratch` is a useful Session-local directory when named explicitly,
but its presence or any `skaha_*` environment variable never enables a cache.

For example, cache whole files under an explicitly named directory. The first
read fetches over the network, and later reads come from that directory:

```python
from fsspec.implementations.cached import WholeFileCacheFileSystem
from canfar.storage import filesystem

vault = filesystem("vault")
cached = WholeFileCacheFileSystem(fs=vault, cache_storage="/scratch/vault-cache")

data = cached.cat_file("/ALMA/test-data/cutouts/test-4d-cube-cutout.fits")
```

Use `SimpleCacheFileSystem` instead when you do not need the expiry and
staleness metadata that `WholeFileCacheFileSystem` keeps. Passing
`cache_storage` a list of directories tries each in order and treats only the
last as writable, so a shared read-only cache can back your own.

### Byte ranges

For an explicit partial read, `vosfs` sends an HTTP `Range` request and uses a
validated `206` response. If the byte endpoint returns `200`, it downloads the
whole object and slices locally. Capability is deployment-specific; do not
infer it from a Storage Identifier's spelling. The staged file-object path is
whole-object, even when `cat_file(path, start, end)` can use a range.

The `blockcache` filesystem remains unavailable over a VOSpace Service because
the opened object is a staged file rather than a ranged buffered reader:

```text
AttributeError: 'StagedReadFile' object has no attribute 'blocksize'
```

Use one explicitly selected cache layer on a local directory you own; do not
silently stack caches or select one from environment variables.

The shown cache wrapper uses the synchronous filesystem returned by
`canfar.storage.filesystem`.

## Output and accepted omissions

Data command stdout belongs to the embedded command; CANFAR does not prepend
the active-Server banner or add JSON/YAML envelopes. Diagnostics are written to
stderr.

The Python equivalent of these commands is documented in
[Data Access](../client/data.md).

This release intentionally provides no FUSE mount, signed-URL extension,
progress display, confirmation prompt, `:/path` or bare-path shorthand,
`active` alias, `canfar storage` alias, recursive removal, or cross-source `mv`
workflow.

## Upstream releases

CANFAR installs pinned, tagged releases of
[`vosfs`](https://github.com/shinybrar/vosfs/releases/tag/v0.8.0) and
[`fsspec-cli`](https://github.com/shinybrar/vosfs/releases/tag/fsspec-cli-v0.7.0).
CANFAR tests its composition, configuration, authentication, and output seams;
exhaustive filesystem-command and backend matrices remain in the upstream
project.
