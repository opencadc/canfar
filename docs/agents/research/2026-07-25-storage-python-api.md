# A Python storage API for CANFAR VOSpace Services

- **Date:** 2026-07-25
- **Repository snapshot:** `ba5493fd` on `feat/vosfs-support`
- **fsspec evaluated:** `2026.6.0`
- **vosfs evaluated:** `0.7.0` (see the 0.8.0 update below)
- **fsspec-cli evaluated:** `0.6.0` (see the 0.7.0 update below)
- **Python:** `3.13.5`
- **Question:** How should `canfar` conveniently expose VOSpace storage for Python API access?

## Update, 2026-07-25 (later the same day): byte ranges now work on `vault`

This note was written against `vosfs` 0.7.0. Upstream
[shinybrar/vosfs#334](https://github.com/shinybrar/vosfs/issues/334), filed from
this research, was fixed in
[#335](https://github.com/shinybrar/vosfs/issues/335) and released as
`vosfs` 0.8.0 / `fsspec-cli` 0.7.0, which `canfar` now pins.

What changed, VERIFIED against the live service on 0.8.0:

- `cat_file(path, start, end)` now sends `Range` and uses a `206` response.
  Observed on `vault`: `Range: bytes=0-2879` -> `HTTP 206`,
  `Content-Range: bytes 0-2879/3542400`, 2880 bytes returned.
- `MMapCache` over a `cat_file` fetcher is now genuinely partial: one ranged
  request, one block of four materialised, zero whole-object fallbacks. Section
  4 below measured the opposite on 0.7.0 and is superseded for `vault`.
- `arc` (Cavern) still serves no ranges and falls back to a whole-object read
  that is sliced. Slices remain correct (VERIFIED), so the "cache whole files"
  guidance still holds there.
- `blockcache` / `CachingFileSystem` still fails with
  `AttributeError: 'StagedReadFile' object has no attribute 'blocksize'`.
  `Range` is honoured for byte reads, not through the file-object path.

The shipped module's public surface is now `identifiers()` and `filesystem()`.
The earlier proposals for dynamic attributes, `fetch()`, and public `sources()`
were superseded: callers pass Storage Identifiers explicitly, materialize with
standard fsspec methods, and the fsspec-cli source mapping remains private
(`_sources()`). No dynamic protocols or module attributes are registered.

Sections 2 and 4 describe the 0.7.0 behaviour and are kept as the historical
record. The single-cache-layer recommendation in the Verdict stands, but its
stated reason ("the second tier is either dead or fictional") now applies only
to `arc`; on `vault` a block cache over `MMapCache` is a real option.

## Verdict

**Ship one module, `canfar/storage.py`, with three public functions and no new
dependency. Build sync by default, async on request, and cache with exactly one
`SimpleCacheFileSystem` layer. Do not build a tiered cache: over `vosfs` 0.7.0 the
second tier is either dead or fictional.**

The recommended surface is:

```python
from canfar.storage import filesystem, fetch, sources
```

- `filesystem(name, *, cache=False, asynchronous=False, token=None, certificate=None)`
  returns a ready `AbstractFileSystem` for one Storage Identifier.
- `fetch(name, path, *, cache=True)` materializes one remote object and returns its
  local `Path`.
- `sources()` is the existing fsspec-cli seam, moved unchanged.

Three findings drive every other decision, and two of them contradict text currently
in `docs/cli/data.md`:

1. **`vosfs` 0.7.0 has no server-side byte ranges.** `_cat_file(path, start, end)`
   downloads the whole object and slices it in memory. A 2880-byte "range" read of a
   3.5 MB file costs the same as reading the file (VERIFIED, §2). Every byte-range
   design — `MMapCache`, `blockcache`, `cache_type=` — is therefore either broken or a
   pessimization.
2. **Only whole-file caching composes.** `simplecache` and `filecache` work. Stacking
   two cache layers builds a stack in which the inner layer never fills and never
   serves (VERIFIED, §5). `cache_storage=["a", "b"]` is a genuine two-location lookup
   but performs no promotion (VERIFIED, §5).
3. **There is no fsspec-native RAM tier over `vosfs`.** `cache_storage="memory://…"`
   is accepted and silently creates a local directory literally named `memory:`
   (VERIFIED, §5). The real RAM tier is the OS page cache over the disk cache
   directory, plus `/dev/shm` on Linux.

The sync/async tension resolves cleanly and is already half-solved in the repository:
build `VOSpaceFileSystem` synchronously, wrap it in the sync cache, and re-expose it
with `AsyncFileSystemWrapper` — the same class `canfar/storage.py:108` already uses
for `local`. This was verified end to end (§4, §9).

`docs/cli/data.md:143-165` should be corrected regardless of whether this API ships.

## Evidence key

Every finding below is marked:

- **VERIFIED** — I executed it in this repository's environment against the live
  `vault` VOSpace Service with `~/.ssl/cadcproxy.pem`, read-only, on 2026-07-25.
- **DOCUMENTED** — I read the source or the published documentation and did not
  execute it.

All experiments used `uv run --no-sync python` from the repository root, targeted only
the two public read-only test objects
(`vault:/ALMA/test-data/cutouts/test-4d-cube-cutout.fits`, 169 920 B, and
`.../test-4d-cube.fits`, 3 542 400 B), and wrote only into the session scratchpad. No
`canfar/` or `tests/` file was modified and no git state was touched.

## 1. Baseline: what exists today

| Element | Location |
| --- | --- |
| `_vospace(name, *, token, certificate)` factory | `canfar/storage.py:31-98` |
| `_local()` async wrapper over `LocalFileSystem` | `canfar/storage.py:101-111` |
| `sources() -> dict[str, AsyncFilesystemSource]` | `canfar/storage.py:114-130` |
| Only consumer | `canfar/cli/data.py:12,22-33` |
| `AsyncFilesystemSource = Callable[[], AbstractAsyncContextManager[AbstractFileSystem]]` | `.venv/lib/python3.13/site-packages/fsspec_cli/_app.py:41-43` |
| Storage Identifier → endpoint + IDP | `canfar/models/config.py:382-395` |
| Credential materialization (async) | `canfar/client.py:234-262` |
| Runtime dependencies | `pyproject.toml:48-65` |

DOCUMENTED. `canfar/storage.py` is not exported from `canfar/__init__.py:16-31`; its
only non-test importer is `canfar/cli/data.py:12`. `docs/cli/data.md:176` states the
release "intentionally provides no public CANFAR storage Python API". The module is
therefore free to be renamed.

## 2. The constraint that dominates everything: no byte ranges

> **Correction (2026-07-25, after review).** The heading below overstates the
> finding: the limitation is in the **client**, not uniformly in the services.
> `vosfs` sends no `Range` header, so every partial read is a whole-object
> download — that part stands and is what makes block caching a pessimization
> today. But the services differ, VERIFIED live against both:
>
> | Service | Backend | Ranged `GET` |
> | --- | --- | --- |
> | `vault` | `minoc` (`ws-cadc.canfar.net/minoc/files/...`) | `206`, `Accept-Ranges: bytes`, `Content-Range: bytes 0-2879/3542400` |
> | `arc` | Cavern | `200`, whole body, no `Accept-Ranges` |
>
> So the Cavern quote below is accurate for `arc` and does not generalize to
> `vault`. Teaching `vosfs` to send `Range` would deliver real byte-range reads
> on `vault` (not on `arc`), which upgrades the upstream ask in section 7 from
> "cosmetic" to genuinely valuable.

DOCUMENTED. `vosfs/staging.py:3-5` states it outright, for Cavern:

> OpenCADC Cavern does not implement HTTP byte ranges, so a seekable read is a
> whole-object download into a disk-backed temporary file.

DOCUMENTED. `vosfs/filesystem.py:547-556` implements `_cat_file` as a whole read
followed by an in-memory slice:

```python
async def _cat_file(self, path, start=None, end=None, **_kwargs):
    """Return one whole-object read sliced with Python half-open semantics."""
    data = await _transfer.read_whole(self, self._strip_protocol(path))
    return data[start:end]
```

`_transfer.read_whole` (`vosfs/_transfer.py:227-240`) joins the full streamed body.
`_transfer.open_read_stream` (`vosfs/_transfer.py:197-224`) sends
`GET` with `transport.IDENTITY_ENCODING` headers and no `Range` header. A grep for
`Range` across the whole installed `vosfs` package returns no hits.

VERIFIED. Timings on `vault:/ALMA/test-data/cutouts/test-4d-cube.fits` (3 542 400 B),
one warm filesystem instance:

| Call | Bytes returned | Wall time |
| --- | --- | --- |
| `cat_file(BIG)` | 3 542 400 | 1.41 s |
| `cat_file(BIG, 0, 2880)` | 2 880 | 1.34 s |
| `cat_file(BIG, size-2880, None)` | 2 880 | 1.21 s |
| `cat_ranges([BIG]*4, 4 starts, 4 ends)` | 4 × 2 880 | 1.16 s |

A 2880-byte head read costs 0.95× a whole-file read. `cat_ranges` is the one genuine
optimization: `vosfs/filesystem.py:594-620` groups ranges by path and
`_read_staged_ranges` (`vosfs/filesystem.py:622-633`) performs **one** whole-object
download per distinct path per call, then slices from the staging file. Four ranges of
one object cost one download, not four.

**Consequence.** Anything that reads a "block" pays for the whole object. This is not
a `vosfs` defect to route around in `canfar`; it is a service-side gap.

### The doc claim that is wrong

`docs/cli/data.md:143-144` says "VOSpace supports ranged reads, so a large cube can be
cached one block at a time rather than downloaded whole", and `:162-163` says "Reading
a FITS header this way transfers a single block instead of the whole file."

VERIFIED false. Driving `MMapCache(blocksize=1<<20, fetcher=lambda s, e: fs.cat_file(BIG, s, e), size=3542400, location=…)`:

| Operation | Wall time | What actually moved |
| --- | --- | --- |
| `mc._fetch(0, 2880)` (one FITS header block) | 1.84 s | full 3 542 400 B download |
| plain `fs.cat_file(BIG)` for comparison | 1.64 s | full 3 542 400 B download |
| three scattered 2880 B reads via `MMapCache` | 4.01 s | **three** full downloads |
| sparse backing file after touching 3 of 4 blocks | — | 3 543 040 B allocated (i.e. full) |

The `MMapCache` mechanics are real — a repeated read of an already-fetched block was
0.000 s, and the on-disk file is genuinely sparse-capable — but over `vosfs` the
fetcher is a whole-object download, so the cache costs *more* network than a single
`cat_file`, and the sparse file fills up anyway. `location=None` (anonymous mmap, RAM)
behaves identically for network cost: 1.40 s for the same header read.

## 3. Import surface: `canfar.storage`, singular

**Recommendation: rename `canfar/storage.py` to `canfar/storage.py` and make it the
public module.**

Rationale, all DOCUMENTED:

- The package's own convention is a singular module name for a plural domain.
  `canfar/__init__.py:16` exports `server` (not `servers`), and `canfar/server.py`
  contains `discover`, `list_servers`, `activate`, `use`. `canfar/sessions.py` is the
  exception, not the rule, and it is a class module.
- The maintainer's suggested import is `from canfar.storage import sources`.
- The module is currently private in every meaningful sense (§1), so the rename costs
  exactly one import line in `canfar/cli/data.py:12` plus the `from canfar import
  storages` references in `tests/test_cli_data.py`. No published API breaks, because
  `docs/cli/data.md:176` says none exists.

Do **not** add a compatibility shim re-exporting `canfar.storage`. There is nothing
to be compatible with.

### What belongs in it — and what does not

| Ask | Recommendation |
| --- | --- |
| Filesystem accessor | `filesystem()` — yes |
| Opener | No new function. `filesystem(name).open(path)` already is the opener. |
| Cache configurator | No object, no builder. One `cache=` parameter on `filesystem()`. |
| Path/URL resolver | **No.** See below. |
| Materialize to a local path | `fetch()` — yes, because the fsspec route is private API (§7) |
| fsspec-cli seam | `sources()`, moved unchanged |

**Reject the path/URL resolver.** VERIFIED: `vos://` URLs do not round-trip. Because
`vosfs` treats everything after the protocol marker as path
(`vosfs/filesystem.py:69-71`, `_strip_protocol` at `:179-188`):

```text
_strip_protocol('vos://cadc-west-01.canfar.net/vault/ALMA/…/test-4d-cube-cutout.fits')
  -> '/cadc-west-01.canfar.net/vault/ALMA/…/test-4d-cube-cutout.fits'
```

The authority is silently swallowed into the path. A `canfar` resolver that emitted
`vos://` URLs would produce strings that look addressable and are not. In Python the
Storage Identifier and the path are already two arguments; a resolver adds a failure mode
and removes nothing. The CLI's `identifier:/path` operand syntax
(`docs/cli/data.md:17-24`) is a *command-line* affordance and should stay there.

## 4. Getting a filesystem, sync and async

The tension is real and I measured both horns.

VERIFIED. **Cache wrappers reject an async `vosfs` instance.**
`SimpleCacheFileSystem(fs=VOSpaceFileSystem(..., asynchronous=True), cache_storage=…)`
constructs, then the first read fails:

```text
RuntimeError: Loop is not running
```

VERIFIED. **A sync `vosfs` instance works inside a running event loop, but blocks
it.** `VOSpaceFileSystem(..., asynchronous=False).cat_file(path)` called from inside
`asyncio.run` succeeded — fsspec's `sync()` dispatches to its own dedicated IO-thread
loop (DOCUMENTED, <https://filesystem-spec.readthedocs.io/en/latest/async.html>), so
it does not hit the "cannot call sync from a running loop" guard. But a ticker
coroutine sleeping every 50 ms recorded **0 ticks** during a 10.60 s call. The caller's
loop is frozen for the duration.

VERIFIED. **`AsyncFileSystemWrapper` over the sync cached stack resolves it.**

```python
inner   = VOSpaceFileSystem(endpoint, certfile=…, asynchronous=False)
cached  = SimpleCacheFileSystem(fs=inner, cache_storage=…)
wrapped = AsyncFileSystemWrapper(cached, asynchronous=True)
```

| Measurement | Result |
| --- | --- |
| `await wrapped._cat_file(SMALL)` cold | 1.87 s, 169 920 B |
| `await wrapped._cat_file(SMALL)` warm | 0.007 s |
| `await wrapped._ls(dir, detail=False)` | 2 entries, correct |
| `await wrapped._info(SMALL)["size"]` | 169 920 |
| ticker ticks during the 1.87 s cold call | **36** (non-blocking) |

DOCUMENTED. `fsspec/implementations/asyn_wrapper.py:11-36` wraps each sync method with
`asyncio.to_thread`, which is why the loop stays responsive. Its class declaration is
`fsspec/implementations/asyn_wrapper.py:39`. `canfar/storage.py:108` already uses this
class for `local`, so it is not a new concept in this codebase. fsspec's own docs call
it "experimental" and warn "Users should not expect this wrapper to magically make
things faster" (<https://filesystem-spec.readthedocs.io/en/latest/async.html>) — the
caution is about throughput, not correctness, and the measurements above are the
throughput answer for this workload.

### The resulting rule

| Request | Build |
| --- | --- |
| `asynchronous=False`, `cache=False` | `VOSpaceFileSystem(..., asynchronous=False)` |
| `asynchronous=False`, cache on | `SimpleCacheFileSystem(fs=<sync vosfs>, ...)` |
| `asynchronous=True`, `cache=False` | `VOSpaceFileSystem(..., asynchronous=True)` — native, best |
| `asynchronous=True`, cache on | `AsyncFileSystemWrapper(SimpleCacheFileSystem(fs=<sync vosfs>), asynchronous=True)` |

Never construct a cache wrapper over an `asynchronous=True` instance.

### Credential materialization from a sync entry point

`canfar/client.py:234` `_materialize_credentials` is `async def`. VERIFIED: it can be
driven from a sync function both outside and inside a running loop using fsspec's own
IO loop, with no `asyncio.run` and no nested-loop guard:

```python
from fsspec.asyn import get_loop, sync
token, certfile = sync(get_loop(), client._materialize_credentials)
```

Outside a loop: 0.57 s (includes X.509 validation). Inside `asyncio.run`: 0.00 s
(credential already warm). This is the smallest correct bridge and adds no dependency.

### One instance is worth keeping

VERIFIED. Per-call latency against `vault`:

| Measurement | Observed |
| --- | --- |
| first `info()` on a fresh instance, 5 fresh instances | 1.65, 0.43, 0.61, 0.56, 0.60 s |
| second `info()` on the same instance | 0.30, 0.34, 0.30, 0.52, 0.36 s |
| whole-object read, 169 920 B, warm instance | ≈ 1.0 s |
| worst first-call outlier observed across all runs | 14.3 s |

The current `sources()` design builds and closes a filesystem per command
(`canfar/storage.py:93-96`), which is right for a CLI. A Python API should hand back a
*reusable* instance so callers pay service-binding discovery once. Note the outliers:
first-call cost is not deterministic, so do not document a fixed number.

DOCUMENTED. `vosfs/filesystem.py:73-75` sets `protocol = "vos"` and `cachable = True`.
VERIFIED: `fsspec.filesystem("vos", endpoint_url=…, certfile=…)` twice returns the
identical object; `skip_instance_cache=True` defeats it. `canfar/storage.py:76,88`
already passes `skip_instance_cache=True`. **Keep that** for the returned instance:
fsspec's instance cache is keyed on the storage options, and a cached instance would
outlive a token refresh.

## 5. Tiered caching: what genuinely composes

### The composition matrix

| Layering | Result | Evidence |
| --- | --- | --- |
| `SimpleCacheFileSystem(fs=vosfs_sync)` | **works**; cold 1.58 s → warm 0.000 s | VERIFIED |
| `WholeFileCacheFileSystem(fs=vosfs_sync)` | **works**; warm 0.000 s | VERIFIED |
| `CachingFileSystem` (blockcache) | **fails**, see §10 | VERIFIED |
| `fs.open(path, cache_type=…)` | **silently ignored** | VERIFIED |
| `filecache::simplecache::vos://` | builds; **middle layer is dead** | VERIFIED |
| hand-stacked `SimpleCache(SimpleCache(vosfs))` | **inner layer never fills** | VERIFIED |
| `cache_storage=[a, b]` | two-location lookup, **no promotion** | VERIFIED |
| `cache_storage="memory://…"` | **silently creates a local dir named `memory:`** | VERIFIED |
| `DirFileSystem(path=…, fs=vosfs)` | works, `async_impl=True` | VERIFIED |
| `SimpleCache(DirFileSystem(vosfs))` | works, 1.34 s cold | VERIFIED |
| `AsyncFileSystemWrapper(SimpleCache(vosfs_sync))` | works, non-blocking | VERIFIED |
| `SimpleCache(fs=vosfs_async)` | `RuntimeError: Loop is not running` | VERIFIED |

### `cache_type=` is accepted and discarded

VERIFIED. Every value in fsspec's cache registry
(`list(fsspec.caching.caches)` = `[None, 'none', 'mmap', 'bytes', 'readahead',
'blockcache', 'first', 'all', 'parts', 'background']`) was passed to
`vosfs.open(path, "rb", cache_type=…)`. All six tested values returned a
`StagedReadFile` with **no `.cache` attribute at all** and identical behaviour. No
warning, no error.

DOCUMENTED, and this is why: `vosfs/filesystem.py:683-690` accepts `block_size` and
`cache_options` marked `# noqa: ARG002 - accepted, non-behavioural`, and
`vosfs/staging.py:59` defines `StagedReadFile(io.BufferedReader)` — a plain buffered
reader, not an `fsspec.spec.AbstractBufferedFile`. fsspec's read-caching machinery only
ever attaches to `AbstractBufferedFile`. **Never document `cache_type` as a `canfar`
tuning knob.**

### URL chaining works, but only with `endpoint_url`, and the middle tier is dead

VERIFIED. `filecache::vos://…` with only `vos={"certfile": …}` fails:

```text
TypeError: VOSpaceFileSystem.__init__() missing 1 required positional argument: 'endpoint_url'
```

It succeeds when the endpoint is supplied in the target options:

```python
fs, path = fsspec.core.url_to_fs(
    f"simplecache::vos://{remote_path}",
    vos={"endpoint_url": endpoint, "certfile": cert, "skip_instance_cache": True},
    simplecache={"cache_storage": cache_dir},
)
```

cold 1.59 s → warm 0.000 s.

VERIFIED, and this is the trap: `filecache::simplecache::vos://` **builds the right
object graph and then bypasses the middle layer**. After a cold read:

```text
outer (filecache)   dir: ['c6de39f6…']
middle (simplecache) dir: []          <- never written
```

Wiping only the outer tier and re-reading took 1.52 s — a network round trip — and the
middle tier stayed empty. Hand-stacking `SimpleCacheFileSystem(fs=SimpleCacheFileSystem(fs=vosfs))`
reproduces it exactly: outer dir populated, inner dir empty.

DOCUMENTED cause: `WholeFileCacheFileSystem` fills itself with
`self.fs.get(getpaths, storepaths)` / `self.fs.get_file(path, fn)`
(`fsspec/implementations/cached.py:673,706`). `get`/`get_file` on the inner cache
filesystem is a straight pass-through to the remote; it does not route through the
inner cache's own `_open`/`cat` path, so the inner cache is never populated. **Chained
cache layers are not a tiering mechanism in fsspec 2026.6.0.**

### `cache_storage` as a list is the only real two-location mechanism

DOCUMENTED. `fsspec/implementations/cached.py:87-91`:

> `cache_storage: str or list(str)` — Location to store files. […] If a list, each
> location will be tried in the order given, but only the last will be considered
> writable.

`fsspec/implementations/cached.py:140` runs `os.makedirs(storage[-1], exist_ok=True)`;
`SimpleCacheFileSystem._check_file` (`:820-826`) scans `self.storage` in order and
returns the first hit.

VERIFIED with `cache_storage=[slow, fast]`:

| Step | Result |
| --- | --- |
| cold read | 1.47 s; written to `fast` (the **last** entry) only |
| move the object to `slow`, empty `fast`, re-read | 0.037 s — served locally from `slow` |
| `fast` after that read | **empty — no promotion** |

So a list gives you *lookup across two directories*, not a hot/cold hierarchy. It is
exactly right for "a shared, pre-populated, read-only cache behind my own writable
one", and it is wrong for "keep hot objects on the fast tier".

### The RAM tier is not real

VERIFIED and worth flagging as a hazard: `SimpleCacheFileSystem(fs=…,
cache_storage="memory://ram")` **constructs without error** and creates a literal local
directory named `memory:` in the process working directory. Nothing about the
`MemoryFileSystem` is involved. (This experiment created such a directory in the
repository root; it was removed and `git status` is clean.)

VERIFIED alternatives:

- `MemoryFileSystem` (`fsspec/implementations/memory.py`) is not a cache wrapper; its
  `store` is a process-global `dict`. Hand-rolling `mem.pipe_file(key, fs.cat_file(p))`
  works (warm read 0.0000 s) but is just a dictionary with extra ceremony, and it is
  process-global mutable state.
- `MMapCache(location=None)` is a genuine anonymous-mmap RAM cache, but its fetcher
  over `vosfs` downloads whole objects (§2), so it is a pessimization here.
- `/dev/shm` does not exist on this Darwin host (VERIFIED); on Linux — including CANFAR
  Sessions — it is a tmpfs and is a perfectly good `cache_storage` value. I could not
  test this on the available machine.

**The honest RAM tier is the OS page cache sitting over your disk cache directory.**
A warm `simplecache` read measured 0.0002 s, which is memory speed, because the kernel
is already holding the file. Adding an explicit RAM layer buys nothing and costs
correctness.

### Per-scenario recommendation

| Scenario | Recommendation |
| --- | --- |
| **(a) Laptop, RAM only** | `filesystem(name, cache=False)` and hold bytes yourself via `fs.cat_file` / `fs.cat_ranges`. If you want a cache, use `cache=True` and let the page cache be the RAM tier. Do not construct `MemoryFileSystem` or `MMapCache`. |
| **(b) Laptop, RAM + second NVMe tier** | One `SimpleCacheFileSystem` pointed at the NVMe: `filesystem(name, cache="/mnt/nvme/canfar/<name>")`. RAM tier = page cache. **Do not stack two cache layers** — the inner one is dead (VERIFIED above). |
| **(c) CANFAR Session, `/scratch` + RAM** | `filesystem(name, cache=True)`, which auto-selects `/scratch/canfar/<name>`. `/scratch` is per-Session NVMe and is cleared at Session end, which is exactly a cache lifetime. If a shared pre-populated read-only cache exists, use `cache=["/shared/canfar-cache", "/scratch/canfar/<name>"]` and document that hits in the shared tier are **not** promoted. |

### Cache-location auto-detection: stdlib only

**Do not add `platformdirs`.** VERIFIED: it is not in `pyproject.toml:48-65`. It
appears in `uv.lock` only as a transitive dependency of `mkdocs-get-deps` (`uv.lock:1256`)
and `virtualenv` (`uv.lock:2183`) — docs and dev groups, not runtime. Adding it to
runtime dependencies to pick a *cache* directory is backwards anyway: `platformdirs`
returns durable user-data/user-cache locations, and what is wanted here is ephemeral
scratch. `tempfile.gettempdir()` already honours `TMPDIR` and is one stdlib call.

VERIFIED sketch (ran correctly on this host, falling back to the temp dir because
`/scratch` is absent):

```python
def _cache_location(name: str) -> Path:
    """Return the default cache directory for one Storage Identifier.

    Prefers the CANFAR Science Platform Server's per-Session ``/scratch`` volume,
    which is fast local disk and is cleared when the Session ends.

    Args:
        name: Storage Identifier of the configured VOSpace Service.

    Returns:
        Path: Writable directory for cached objects.
    """
    scratch = Path("/scratch")
    root = scratch if scratch.is_dir() and os.access(scratch, os.W_OK) else Path(tempfile.gettempdir())
    return root / "canfar" / name
```

Keying by Storage Identifier matters: `fsspec`'s cache mapper hashes the *stripped* path
(`fsspec/implementations/cached.py:627`), which does not include the endpoint, so
`arc:/x` and `vault:/x` would otherwise collide in one directory.

## 6. `WholeFileCacheFileSystem` vs `SimpleCacheFileSystem`

**Recommend `SimpleCacheFileSystem`.**

DOCUMENTED. `fsspec/implementations/cached.py:791-805`: `SimpleCacheFileSystem`
"only copies whole files, and does not keep any metadata about the download time or
file details. It is therefore safer to use in multi-threaded/concurrent situations."
fsspec's feature docs state "Only 'simplecache' is guaranteed thread/process-safe"
(<https://filesystem-spec.readthedocs.io/en/latest/features.html#caching-files-locally>).
Its `__init__` (`:811-818`) forces `cache_check`, `expiry_time` and `check_files` to
`False`.

VERIFIED: both work; both give warm reads at 0.000 s. `WholeFileCacheFileSystem` keeps
a JSON metadata sidecar (a `cache` file appears alongside the objects) and computes
`self.fs.ukey(path)` on every miss (`fsspec/implementations/cached.py:634`), which is
an extra `info` round trip. A `/scratch` cache that dies with the Session does not need
expiry metadata. Expose `WholeFileCacheFileSystem` only if a user asks for expiry — do
not put it in the first API.

## 7. "Get a file location"

VERIFIED results for materializing a remote object to a local path:

| Approach | Works over `vosfs`? |
| --- | --- |
| `fsspec.open_local("vos://…")` | **No.** `ValueError: open_local can only be used on a filesystem which has attribute local_file=True` |
| `fsspec.open_local("simplecache::vos://…", vos={"endpoint_url": …}, simplecache={"cache_storage": …})` | **Yes** — 1.64 s, returns the cache path |
| `fs.get_file(remote, local)` | **Yes** — writes the exact 169 920 B; explicit destination |
| `SimpleCacheFileSystem.open(path).name` | **Yes** — is the local cache path, exists on disk |
| `SimpleCacheFileSystem._check_file(path)` | **Yes** — returns the local path directly, `None` before the first read |
| `WholeFileCacheFileSystem._check_file(path)` | Returns a `(detail, path)` **tuple**, not a string |
| `LocalFileOpener` | Not reachable — it is `LocalFileSystem`'s own file class, never produced by a cache layer over `vosfs` |

DOCUMENTED. `fsspec/core.py:544-549` is the `local_file` gate;
`fsspec/implementations/cached.py:560,808` set `local_file = True` on
`WholeFileCacheFileSystem` and `SimpleCacheFileSystem`. Bare `vosfs` sets nothing, hence
the failure. `WholeFileCacheFileSystem._open` (`:730-738`) returns a builtin
`open(fn, mode)` — a real `_io.BufferedReader` on a real local path — which is why
`.name` is usable.

**Recommendation.** Expose `fetch()`. The two working routes are `fsspec.open_local`
with a chained URL — which requires callers to hand-assemble `vos://` strings and
`endpoint_url`, exactly the resolver footgun rejected in §3 — and `_check_file`, which
is private API. A four-line public function is cheaper than teaching either:

```python
def fetch(name: str, path: str, *, cache: bool | str | Path = True) -> Path:
    """Materialize one VOSpace object locally and return its path.

    Args:
        name: Storage Identifier of the configured VOSpace Service.
        path: Absolute path within that VOSpace Service.
        cache: Cache location, or ``True`` for the default (see ``filesystem``).

    Returns:
        Path: Local path holding the object's bytes.
    """
    fs = filesystem(name, cache=cache or True)
    fs.cat_file(path)          # populates the cache
    return Path(fs._check_file(path))
```

If reaching into `_check_file` is unacceptable, use `fs.get_file(path, destination)`
with an explicit destination instead and drop the cache-path form — but then the caller
owns cleanup, and repeat calls re-download. Prefer the cache-backed form; the private
attribute is one call site in one file and is trivially covered by a test.

## 8. Sync-first, async-first, or both

**Sync-first, with `asynchronous=True` as a keyword. Not two classes, not two modules.**

Reasons:

1. Caching only exists in sync form (§4, §5). A sync-first API means the common case —
   "read this FITS file, cache it on `/scratch`" — is one call with no wrapper.
2. Astronomy consumers of a materialized path (`astropy.io.fits.open`,
   `numpy.load`, `pandas.read_*`) are synchronous.
3. The async path is genuinely better when uncached — native `VOSpaceFileSystem(...,
   asynchronous=True)` was VERIFIED working for `_info` and `_ls` — so it must remain
   available, and `sources()` depends on it.
4. `canfar` already ships sync/async parity elsewhere (`Session` / `AsyncSession`,
   `AGENTS.md:58`), but that parity is for a hand-written client. Here both paths are
   the same fsspec object with one constructor flag; two classes would be pure
   duplication.

### Relationship to `sources()`

`sources()` moves to `canfar/storage.py` **unchanged**. Its contract with fsspec-cli is
`Callable[[], AbstractAsyncContextManager[AbstractFileSystem]]`
(`fsspec_cli/_app.py:41-43`), it must yield an async filesystem, and it must build and
`aclose()` per command so a listing cache cannot outlive its command
(`canfar/storage.py:93-96`, `docs/cli/data.md:106-110`).

Refactor `_vospace` to delegate to the new `filesystem()` rather than duplicating
construction:

```python
def _vospace(name, *, token=None, certificate=None) -> AsyncFilesystemSource:
    @asynccontextmanager
    async def source() -> AsyncIterator[AbstractFileSystem]:
        fs = filesystem(name, token=token, certificate=certificate, asynchronous=True)
        try:
            yield fs
        finally:
            await fs.aclose()
    return source
```

Do **not** put a cache layer behind `sources()`. `fsspec-cli` performs writes
(`cp`, `mkdir`, `rm`); `SimpleCacheFileSystem` has write semantics of its own
(`fsspec/implementations/cached.py:800-803`, `WriteCachedTransaction`) that were not
evaluated here, and a CLI that silently served stale bytes would be a defect. The CLI's
existing per-command listing cache is the right amount of caching for it.

## 9. Recommended API sketch

`canfar/storage.py` — three public functions, one private helper, no new dependency.
Every element below was exercised in the prototype (VERIFIED, §4/§5/§7).

```python
"""Public access to configured VOSpace Services and the local filesystem."""

from __future__ import annotations

import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fsspec.asyn import get_loop, sync
from fsspec.implementations.asyn_wrapper import AsyncFileSystemWrapper
from fsspec.implementations.cached import SimpleCacheFileSystem
from fsspec.implementations.local import LocalFileSystem

from canfar.client import HTTPClient
from canfar.exceptions.context import AuthContextError
from canfar.models.config import Configuration

_LISTINGS_EXPIRY_SECONDS = 30
_LISTINGS_MAX_PATHS = 1000

CacheLocation = bool | str | Path | Sequence[str | Path]


def filesystem(
    name: str,
    *,
    cache: CacheLocation = False,
    asynchronous: bool = False,
    token: str | SecretStr | None = None,
    certificate: Path | None = None,
) -> AbstractFileSystem:
    """Return an authenticated filesystem for one Storage Identifier.

    Args:
        name: Storage Identifier of the configured VOSpace Service.
        cache: ``False`` for no caching, ``True`` for the default cache
            directory, a path for an explicit one, or a sequence of paths
            tried in order where only the last is writable.
        asynchronous: Return an async filesystem whose coroutine hooks are
            awaited directly. Sync methods are unavailable on the result.
        token: Runtime bearer token, preferred over any saved credential.
        certificate: Runtime X.509 certificate path.

    Returns:
        AbstractFileSystem: A ready filesystem rooted at the VOSpace Service.

    Raises:
        AuthContextError: If no usable credential exists for the Identity
            Provider that owns this VOSpace Service.
    """


def fetch(
    name: str,
    path: str,
    *,
    cache: CacheLocation = True,
) -> Path:
    """Materialize one VOSpace object locally and return its path."""


def sources() -> dict[str, AsyncFilesystemSource]:
    """Build the mapped storage sources for one data command invocation."""
    # unchanged from canfar/storage.py:114-130
```

Construction body, matching the rule table in §4:

```python
    config = Configuration()
    endpoint, idp = config._resolve_storage(name)
    try:
        client = HTTPClient(config=config, authentication_idp=idp, url=endpoint, ...)
        token_value, certfile = sync(get_loop(), client._materialize_credentials)
    except (KeyError, OSError, TypeError, ValueError):
        raise AuthContextError(idp, "Credential cannot be used. Run 'canfar login' for this IDP.") from None

    from vosfs import VOSpaceFileSystem

    credential = {"token": token_value} if token_value is not None else {"certfile": certfile}
    remote = VOSpaceFileSystem(
        endpoint,
        asynchronous=asynchronous and not cache,
        skip_instance_cache=True,
        use_listings_cache=True,
        listings_expiry_time=_LISTINGS_EXPIRY_SECONDS,
        max_paths=_LISTINGS_MAX_PATHS,
        **credential,
    )
    if not cache:
        return remote
    storage = _cache_location(name) if cache is True else cache
    cached = SimpleCacheFileSystem(fs=remote, cache_storage=_as_storage(storage))
    return AsyncFileSystemWrapper(cached, asynchronous=True) if asynchronous else cached
```

Notes on the shape:

- `cache` is a single parameter, not a configurator object or a `CacheConfig` model.
  A Pydantic model would be a data model with no persisted state and no validation
  beyond "is this a path", which the filesystem call already performs.
- `asynchronous=True` with `cache` truthy must build the *sync* `vosfs` and wrap
  (`asynchronous=asynchronous and not cache` above) — this is the single most
  error-prone line and deserves a comment and a test.
- `skip_instance_cache=True` is retained deliberately (§4).
- No `Storage`/`VOSpace` class. Every method a caller could want is already on
  `AbstractFileSystem`.

### Usage the docs should show

```python
from canfar.storage import fetch, filesystem

# One-off read.
vault = filesystem("vault")
header = vault.cat_file("/ALMA/test-data/cutouts/test-4d-cube.fits", 0, 2880)

# Repeated reads on a Science Platform Server Session: cache under /scratch.
vault = filesystem("vault", cache=True)
data = vault.cat_file("/ALMA/test-data/cutouts/test-4d-cube.fits")   # 1.6 s
again = vault.cat_file("/ALMA/test-data/cutouts/test-4d-cube.fits")  # 0.0002 s

# Hand a local path to a library that only takes paths.
from astropy.io import fits
with fits.open(fetch("vault", "/ALMA/test-data/cutouts/test-4d-cube.fits")) as hdul:
    ...

# Concurrent async reads, uncached.
arc = filesystem("arc", asynchronous=True)
try:
    sizes = await asyncio.gather(*(arc._info(p) for p in paths))
finally:
    await arc.aclose()
```

The `cat_file(path, 0, 2880)` in the first example is honest — it returns the right
bytes — but §2 means it costs a full download. Say so in the docs.

## 10. Upstream gaps

### Gap 1 — `blockcache` is unusable (root cause: no ranged reads)

VERIFIED exact error, from `CachingFileSystem(fs=vosfs, cache_storage=…)` on both
`.open(path).read(100)` and `.cat_file(path)`:

```text
AttributeError: 'StagedReadFile' object has no attribute 'blocksize'
```

DOCUMENTED cause: `fsspec/implementations/cached.py:702` reads
`block = getattr(f, "blocksize", 5 * 2**20)` defensively, but the failing access is on
the `CachingFileSystem` path, which assumes the target's file object is an
`AbstractBufferedFile` with `.blocksize` and `.cache`. `vosfs/staging.py:59` returns an
`io.BufferedReader` subclass instead.

**What would unblock it, in order:** (1) OpenCADC Cavern implementing HTTP `Range` on
the negotiated data endpoint; (2) `vosfs` sending `Range` headers from `_cat_file`;
(3) `vosfs._open` returning an `fsspec.spec.AbstractBufferedFile` subclass backed by
those ranged reads. Adding a `blocksize` attribute alone would convert a loud failure
into a silent whole-object-per-block pessimization — do not ask for that.

**Until then, `canfar` should not offer a block-cache option at all.**

### Gap 2 — fsspec accepts a URL as `cache_storage`

VERIFIED. `cache_storage="memory://ram"` is `os.makedirs`'d verbatim
(`fsspec/implementations/cached.py:140`), creating a directory named `memory:`. No
error, no warning. Worth an upstream issue; in the meantime, `canfar` should reject
any `cache` value containing `://` with a clear message.

### Gap 3 — chained cache layers silently no-op

VERIFIED (§5). `filecache::simplecache::X` constructs a three-layer stack in which the
middle layer never caches. Worth an upstream issue. `canfar` should never document
chained cache URLs.

## 11. Documentation changes required

If this API ships:

- `docs/cli/data.md:176` — "This release intentionally provides no public CANFAR
  storage Python API" must be updated; the FUSE mount, signed-URL, progress display and
  the other listed omissions still stand.
- A new `docs/client/storage.md` for `canfar.storage`.

**Independently of this API**, `docs/cli/data.md:143-165` is factually wrong and should
be corrected now:

- `:143-144` "VOSpace supports ranged reads, so a large cube can be cached one block at
  a time rather than downloaded whole" — VERIFIED false for `vosfs` 0.7.0.
- `:162-163` "Reading a FITS header this way transfers a single block instead of the
  whole file, and a second read of the same range is served from `/scratch`" — the
  second clause is true; the first is VERIFIED false. The `MMapCache` example moves
  3 542 400 B to return 2 880 B, and three scattered header reads cost three full
  downloads (4.01 s versus 1.64 s for reading the file once).
- `:164-165` "Ranged reads help most on large files; on small ones the per-request
  VOSpace transfer negotiation dominates" — the ordering is inverted. Ranged reads help
  on *no* file size today; larger files are strictly worse.

The correct advice for large-cube access with `vosfs` 0.7.0 is: read the object once
into a `simplecache` directory on `/scratch` and slice locally, or use `cat_ranges`,
which does group multiple ranges of one object into a single download
(`vosfs/filesystem.py:594-620`, VERIFIED: 4 ranges in 1.16 s).

## 12. What I could not verify

- **`/dev/shm` as `cache_storage` on a CANFAR Session.** `/dev/shm` does not exist on
  this Darwin host (VERIFIED absent). The mechanism is a plain directory path so there
  is no fsspec reason it would fail, but the tmpfs sizing and eviction behaviour on a
  Science Platform Server Session is untested.
- **`/scratch` on a real Session.** Auto-detection was exercised only through its
  fallback branch; `Path("/scratch").is_dir()` was `False` here.
- **Write paths through a cache layer.** All experiments were read-only against `vault`
  by design. `SimpleCacheFileSystem`'s write/commit semantics
  (`fsspec/implementations/cached.py:800-803`) were read, not executed. This is why §8
  recommends keeping caching out of `sources()`.
- **OIDC credentials.** Only the X.509 branch of `_materialize_credentials` was
  exercised (`~/.ssl/cadcproxy.pem`). The OIDC-refresh branch
  (`canfar/client.py:252-259`) is `async` and was not driven through
  `fsspec.asyn.sync`; it should be covered by a test before release.
- **`arc`.** Every live measurement used `vault`. `arc` was not touched, per the
  read-only constraint.
- **First-call latency stability.** Observed first-I/O costs ranged from 0.43 s to
  14.3 s with no reproducible pattern. Cause not established; do not publish a number.

## Primary sources

- `canfar/storage.py`, `canfar/cli/data.py`, `canfar/client.py`,
  `canfar/models/config.py`, `pyproject.toml`, `uv.lock`, `CONTEXT.md`, `AGENTS.md`,
  `docs/cli/data.md` (repository snapshot `ba5493fd`)
- `.venv/lib/python3.13/site-packages/vosfs/filesystem.py`, `.../vosfs/staging.py`,
  `.../vosfs/_transfer.py` (vosfs 0.7.0)
- `.venv/lib/python3.13/site-packages/fsspec/implementations/cached.py`,
  `.../fsspec/implementations/asyn_wrapper.py`, `.../fsspec/implementations/dirfs.py`,
  `.../fsspec/implementations/memory.py`, `.../fsspec/caching.py`, `.../fsspec/core.py`
  (fsspec 2026.6.0)
- `.venv/lib/python3.13/site-packages/fsspec_cli/_app.py` (fsspec-cli 0.6.0)
- [fsspec: Features — caching files locally](https://filesystem-spec.readthedocs.io/en/latest/features.html#caching-files-locally)
- [fsspec: Features — URL chaining](https://filesystem-spec.readthedocs.io/en/latest/features.html#url-chaining)
- [fsspec: Async](https://filesystem-spec.readthedocs.io/en/latest/async.html)
- [vosfs v0.7.0](https://github.com/shinybrar/vosfs/releases/tag/v0.7.0)
- [fsspec-cli v0.6.0](https://github.com/shinybrar/vosfs/releases/tag/fsspec-cli-v0.6.0)
