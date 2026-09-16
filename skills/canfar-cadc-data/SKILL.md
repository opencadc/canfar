---
name: canfar-cadc-data
description: >
  CADC astronomical archive discovery and download from CANFAR using the CADC
  search portal, cadcget/cadcdata, TAP/cadctap, and persistent project storage.
  Use for archive observations, survey FITS, CADC catalogs, or TAP queries; not
  for a user's VOSpace files.
---
# CADC archive data

**CANFAR** provides compute, Sessions, and user/project storage. **CADC archives**
provide curated observatory and survey holdings. The same identity can be used,
but archive identifiers are not VOSpace paths.

Archive search: [CADC](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/)

## Simple workflow

1. Discover observations/files in the CADC search interface.
2. Download into persistent project storage when collaborators or later Sessions
   need the data.
3. Stage hot working files into `/scratch` inside one Session.
4. Copy results back to persistent storage or a publication VOSpace service.

## `cadcget` syntax

The current `opencadc/cadctools` implementation accepts one Storage Inventory
identifier such as `COLLECTION/file` (or `cadc:COLLECTION/file`) and an optional
output path. It does **not** take separate archive-ID and file-ID positional
arguments.

```bash
cadcget GEMINI/N20220825S0383.fits
cadcget cadc:CFHT/700000o.fits.fz --output /arc/projects/mygroup/raw/
```

Check the installed version's exact options with `cadcget --help`. Use
`cadc-get-cert` when the archive product requires authenticated CADC access.

## TAP and Python

Use `cadctap` for catalog/service queries and `cadcdata.StorageInventoryClient`
for programmatic file retrieval. Service schemas and access policy are archive
specific; inspect TAP metadata rather than inventing columns.

```python
from cadcdata import StorageInventoryClient

client = StorageInventoryClient()
client.cadcget("cadc:CFHT/700000o.fits.fz", "/scratch/700000o.fits.fz")
```

## Archive versus VOSpace

| | CADC archive | User/project VOSpace |
| --- | --- | --- |
| Content | Curated observations/catalogs | User or team files |
| Address | Collection/file identifiers, TAP rows | Storage Identifier paths or legacy `vos:` |
| Current tools | `cadcget`, `cadcdata`, `cadctap` | `canfar data`, `canfar.storage`, legacy `vcp` |

## Agent rules

1. Do not transform an archive identifier into a `vos:` path.
2. Large/valuable downloads go to a persistent project allocation, not personal home.
3. Confirm archive access policy before assuming authentication alone grants a product.

Related: `canfar-storage`, `canfar-transfers`, `canfar-vospace`
