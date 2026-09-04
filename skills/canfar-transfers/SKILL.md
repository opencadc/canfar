---
name: canfar-transfers
description: >
  CANFAR data transfers between a laptop, Session scratch, persistent POSIX
  storage, and VOSpace Services using the Portal, canfar data, fsspec, legacy
  vcp/vsync, or site-provided SSHFS. Use when moving files, uploading FITS,
  syncing data, or planning large transfers.
---
# Data transfers

Docs: [Data transfers](https://www.opencadc.org/canfar/latest/platform/storage/transfers/)

## Choose a method

| Scenario | Method |
| --- | --- |
| A few files, browser user | Site Storage UI when available |
| Scripted local ↔ VOSpace | `canfar data cp` with Storage Identifiers |
| Python/scientific library | `canfar.storage` fsspec filesystem |
| Existing CADC VOSpace workflow | `vcp` / `vsync` |
| Active Session work | POSIX `cp` between `/scratch` and persistent storage |
| Mounted external filesystem | `rsync` to the site-provided SSHFS mount |

Choose by retryability and number of files, not a universal size threshold.
Browser limits, transfer endpoints, and SSH access are deployment-specific.

## Inside a session

CADC example:

```bash
cp /arc/projects/mygroup/raw/large.fits /scratch/
# ... process ...
cp /scratch/results.csv /arc/projects/mygroup/results/
```

## Current `canfar data` CLI

```bash
canfar login
canfar data cp local:/absolute/path/local.fits arc:/projects/mygroup/data/local.fits
canfar data ls -lh arc:/projects/mygroup/data/local.fits
canfar data cp arc:/projects/mygroup/results/result.fits vault:/myuser/releases/result.fits
```

The client verifies destination metadata for copies. A recursive copy is not a
snapshot or atomic operation; inspect the destination before removing a source.

## Legacy VOSpace tools

```bash
cadc-get-cert -u $USER
vcp ./local.fits vos:myuser/incoming/
vsync /arc/projects/mygroup/out vos:myuser/published/
```

Use these when the user already has a CADC `vos:` workflow or needs a feature not
yet exposed by `canfar data`. See `canfar-vospace` for exact syntax.

## Low-level HTTPS (CADC only)

```bash
cadc-get-cert --user $USER
curl --cert ~/.ssl/cadcproxy.pem --upload-file file.fits \
  https://ws-uv.canfar.net/arc/files/projects/mygroup/file.fits
```

This is a service-specific escape hatch, not the default recommendation. Do not
copy this host to another site. Prefer `canfar data` and discovered Storage
Identifiers.

## SSHFS (from your laptop)

CADC provides an SSH/SSHFS path to ARC. Follow the current endpoint and key setup
in [Filesystem access](https://www.opencadc.org/canfar/latest/platform/storage/filesystem/).
Do not assume another deployment exposes SSH.

## Agent rules

1. Never leave the only copy on `/scratch` — session end deletes it.
2. Use the site's publication VOSpace for releases and its persistent project
   storage (CADC: `/arc/projects`) for active team work.
3. For many files or long transfers, use a resumable/synchronizing workflow and
   verify counts/checksums or destination metadata before cleanup.
