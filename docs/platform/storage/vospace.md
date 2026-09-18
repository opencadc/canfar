<span id="vospace"></span>

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

<span id="vospace-overview"></span>
<span id="what-is-vospace"></span>
<span id="vault-vospace-vs-arc-vospace-vs-scratch"></span>
<span id="web-interface"></span>
<span id="accessing-vospace"></span>
<span id="web-interface-features"></span>
<span id="installation"></span>
<span id="basic-operations"></span>
<span id="directory-operations"></span>
<span id="advanced-operations"></span>
<span id="bulk-operations"></span>
<span id="data-cutouts-and-processing"></span>
<span id="basic-setup"></span>
<span id="batch-processing"></span>
<span id="metadata-management"></span>
<span id="progress-monitoring"></span>
<span id="sharing-and-collaboration"></span>
<span id="setting-up-sharing"></span>
<span id="public-urls"></span>
<span id="collaboration-workflows"></span>
<span id="multi-institutional-project"></span>
<span id="data-publication"></span>
<span id="integration-with-astronomical-tools"></span>
<span id="integration-with-archives"></span>
<span id="caching-and-local-mirrors"></span>
<span id="monitoring-and-logging"></span>
<span id="troubleshooting"></span>
<span id="common-issues"></span>
<span id="debugging-and-diagnostics"></span>
<span id="related-storage-docs"></span>
<span id="bulk-operations_1"></span>
<span id="vault-vospace-api"></span>
<span id="arc-vospace-api-outside-canfar"></span>
<span id="basic-usage"></span>
<span id="advanced-operations_1"></span>
<span id="automation-workflows"></span>
<span id="batch-processing-script"></span>
<span id="monitoring-and-logging_1"></span>
<span id="error-handling"></span>
<span id="caching-strategy"></span>
<span id="integration-examples"></span>
<span id="with-astropy"></span>
<span id="with-batch-jobs"></span>
<span id="troubleshooting_1"></span>
<span id="common-issues_1"></span>

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

<span id="command-line-interface"></span>
<span id="command-line-sharing"></span>

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

<span id="python-api"></span>
<span id="advanced-python-usage"></span>
<span id="python-api_1"></span>

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

<span id="file-operations"></span>
<span id="file-operations_1"></span>
<span id="file-management"></span>
<span id="file-operations_2"></span>
<span id="fits-file-handling"></span>
<span id="performance-and-optimization"></span>
<span id="transfer-performance"></span>
<span id="network-and-transfer-issues"></span>
<span id="file-operations_3"></span>
<span id="transfer-progress"></span>
<span id="performance-optimization"></span>
<span id="parallel-transfers"></span>

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

<span id="sharing-and-permissions"></span>
<span id="authentication"></span>
<span id="permission-management"></span>
<span id="permission-levels"></span>
<span id="owner-permissions"></span>
<span id="group-permissions"></span>
<span id="public-permissions"></span>
<span id="authentication-problems"></span>
<span id="permission-errors"></span>

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

<span id="legacy-vostools"></span>

## Legacy vostools

The `vos` package provides the older `vls`, `vcp`, `vsync`, `vmkdir`, `vrm`,
and `vchmod` commands. Use `canfar data` for new work. Keep vostools for an
existing script, for one-way directory synchronisation with `vsync`, and for
setting VOSpace permissions with `vchmod`, which `canfar data` does not do.

```bash
pip install vos
```

vostools reads the certificate at `~/.ssl/cadcproxy.pem`, the file that
`canfar login cadc` writes and keeps valid for 30 days. Without the CANFAR
client, `cadc-get-cert -u USERNAME` writes the same file, valid for 10 days
unless you pass `--days-valid`. Every command also accepts `--certfile PATH` or
`--token TOKEN`; with neither, it tries `~/.netrc` and then anonymous access.

`vos:` and `vault:` both name CADC Vault. Any other scheme names the CADC
service of that name, so ARC is `arc:`. The long forms are
`vos://cadc.nrc.ca~vault/PATH` and `vos://cadc.nrc.ca~arc/PATH`.

| Command | What it does |
| --- | --- |
| `vls -l vos:USER/` | List one node in detail. `-h` prints human-readable sizes; help is `--help`. |
| `vcp input.fits vos:USER/data/` | Upload. `vcp vos:USER/data/input.fits ./` downloads. |
| `vcp "vos:USER/data/*.fits" ./` | Download by pattern; quote it so the shell leaves it alone. |
| `vsync --recursive ./run-42 arc:projects/PROJECT/run-42` | Synchronise a local directory to VOSpace, one way. `--nstreams N` sets parallel streams (5 by default, at most 30). |
| `vmkdir -p vos:USER/a/b` | Create a directory and its parents. |
| `vchmod g+r vos:USER/data "GROUP"` | Let a group read. `g+w` grants write, and `g+rw` takes the read group and then the write group. |
| `vchmod o+r vos:USER/data` | Make a node public; `o-r` reverses it. `-R` applies a mode recursively. |

`vcp` always copies recursively and cannot copy between two VOSpace services;
download and upload instead, or use `canfar data cp`, which can. To give
several groups the same permission, pass them as one quoted, space-separated
argument, such as `"GROUP1 GROUP2"`, up to four groups.

## Related guides

- [Storage overview](index.md)
- [Filesystem and Python tools](filesystem.md)
- [Data transfers](transfers.md)
- [Permissions](../permissions.md)
