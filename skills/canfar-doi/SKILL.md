---
name: canfar-doi
description: >
  CADC CANFAR Data Publication Service workflow for research-data DOIs: reserve
  a record, prepare/upload the assigned Vault package, arrange review access,
  publish through DataCite, and preserve the frozen release. Use for CADC DPS,
  data citation, peer-review data access, or DOI publication; do not assume every
  Skaha deployment provides this service.
---
# CADC Data Publication Service (DOI)

This is a **CADC deployment service**, not a generic Skaha or `canfar` client
capability. Confirm the Data Publication link exists in the site's Portal before
offering this workflow. CADC currently exposes it at
[canfar.net/citation](https://www.canfar.net/citation/).

The service implementation is outside the OpenCADC repositories mapped by the
architecture skill; its live UI/API is authoritative. Public prose can lag, so
verify irreversible actions and current fields in the service before proceeding.

## Workflow

1. **Request/reserve** a DOI record in DPS and note its assigned Vault data path.
2. **Prepare the package** with data, README, schemas/calibration notes, software
   versions, checksums, and any reuse/license information required by the service.
3. **Upload and verify** every file at the assigned path. Use the browser for a
   few files or `canfar data`/legacy `vcp` for larger packages.
4. **Arrange reviewer access** through CADC support if the package must remain
   private during peer review.
5. **Review the landing metadata and package**, then publish only when ready.
6. **Record the data DOI** in the paper and connect the paper DOI/reference when
   the service/support workflow permits.

## Irreversible boundary

Publishing registers the DOI through DataCite and is expected to freeze the data
directory. Immediately before publishing, re-check the live confirmation text,
file list, checksums, authors, title, and citation metadata. Do not click Publish
or tell an agent to do so without the user's explicit authorization.

After publication, treat the release as immutable. Corrections or metadata
changes go through `support@canfar.net` and may require a new version/record.

## Upload choices

| Situation | Route |
| --- | --- |
| A few small files | DPS/Storage UI |
| Scripted upload | `canfar data cp local:/... vault:/assigned/path/...` |
| Existing CADC VOSpace workflow | `vcp` / `vsync` to the exact assigned path |

Never guess the DOI's Vault path from an example. Use the path created by the
live service.

Related: `canfar-vospace`, `canfar-transfers`, `canfar-cadc-data`
