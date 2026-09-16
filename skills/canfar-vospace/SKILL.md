---
name: canfar-vospace
description: >
  CANFAR VOSpace Services: discovered Storage Identifiers, CADC Vault and ARC,
  Cavern, canfar data, Python fsspec, and legacy vos URIs/vcp/vls/vsync/vchmod.
  Use for Vault, VOSpace, remote storage APIs, ACL sharing, or publication data.
---
# VOSpace (Vault & ARC)

Docs: [VOSpace guide](https://www.opencadc.org/canfar/latest/platform/storage/vospace/)

VOSpace is an IVOA service API, not one universal disk. After `canfar login`, a
Science Platform Server can expose several VOSpace Services, each addressed by a
discovered **Storage Identifier**. CADC normally exposes `arc` and `vault`; the
SRCNet client prefers a primary service with the registry leaf `cavern`.

## When to use which

| | **CADC Vault** | **Cavern/ARC** | **Scratch** |
| --- | --- | --- | --- |
| Purpose | Archive, share, publish | Active team work | Temp compute |
| Durability | CADC publication/archive policy | Deployment policy | None |
| Speed | Slower | Medium (POSIX) | Fastest |
| Public sharing | Supported through service ACLs/links | Deployment-specific | No |
| Access | Web + `vos:` API | POSIX + VOSpace view | Session only |

**Cavern** is OpenCADC's VOSpace-over-POSIX implementation. **ARC** is CADC's
deployed service/mount name. They are related concepts, not interchangeable path
names on every site.

## Web managers (CADC example)

- [Vault](https://www.canfar.net/storage/vault/list/)
- [ARC VOSpace view](https://www.canfar.net/storage/arc/list/)

Upload, permissions (right-click → Properties), public links.

## Current CLI

Prefer the current `canfar data` interface when its Storage Identifiers cover the
operation. Operands always include an identifier and absolute service path:

```bash
canfar login cadc
canfar data ls -lh arc:/home/$USER
canfar data cp local:/absolute/path/table.fits vault:/myuser/releases/v1/table.fits
canfar data cp vault:/myuser/in/large.fits arc:/projects/mygroup/raw/large.fits
```

Cross-service `mv` and recursive `rm` are intentionally unsupported. Copy, verify
the destination, and remove the source separately only when the user authorizes
deletion.

## Legacy CADC VOSpace tools

```bash
canfar login
vls vos:myuser
vls vos:myuser/projects/
vcp ./table.fits vos:myuser/releases/v1/
vcp vos:myuser/in/large.fits /scratch/
vsync /arc/projects/mygroup/out vos:myuser/published/
vmkdir vos:myuser/newdir
vchmod g+w vos:myuser/shared/ "my-cadc-group"
```

`vchmod g+r` or `g+w` requires the applicable CADC group argument. The
`cadc-get-cert` default is currently 10 days and writes
`~/.ssl/cadcproxy.pem`; renew rather than embedding credentials.

## Python API

The current client resolves credentials and VOSpace endpoints into fsspec
filesystems:

```python
from canfar.storage import filesystem, identifiers

print(identifiers())
vault = filesystem("vault")
with vault.open("/myuser/releases/v1/table.fits", "rb") as handle:
    header = handle.read(2880)
```

Use `/scratch` as a cache/materialization target for libraries that require a
local path. See `canfar-python-client` for API details.

## Sharing model

VOSpace ACLs are service metadata, not ordinary POSIX mode bits even when the
same data also appears through a filesystem mount. Use the site's Storage UI or
the exact `vchmod` syntax for group/public permissions; verify with `vls -l`.

## ARC via VOSpace URI

```bash
canfar data cp local:/absolute/path/file.fits arc:/projects/mygroup/incoming/file.fits
# Legacy vostools: scheme vos: is Vault. ARC uses the arc: shortcut or vos:// form:
vcp file.fits arc:/projects/mygroup/incoming/
# vcp file.fits vos://cadc.nrc.ca~arc/projects/mygroup/incoming/
```

CADC POSIX path `/arc/projects/mygroup/` and the VOSpace view of the same allocation.

## Large transfers

Use `vcp`/`vsync`, not web UI — see `canfar-transfers`.

## Publication

DOI workflow uses Vault — `canfar-doi`.

## Agent rules

1. Use a publication VOSpace for **citation-ready** releases; use persistent
   project storage (CADC: `/arc/projects`) for **active** collaboration.
2. Storage Identifier paths work across Sessions and from authorized external clients.
3. Do not invent `arc`, `vault`, or `cavern`; use discovered identifiers.

Related: `canfar-cadc-data` (archives ≠ your vos space)
