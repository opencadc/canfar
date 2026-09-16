---
name: canfar-storage
description: >
  CANFAR storage: Session scratch, persistent personal and project POSIX mounts,
  discovered VOSpace Storage Identifiers, persistence, data layout, and external
  access. Use when asking where to save files, sharing between Sessions, scratch
  vs ARC/Cavern, or organizing data.
---
# CANFAR storage

Docs: [Storage systems](https://www.opencadc.org/canfar/latest/platform/storage/)

## User-facing tiers

| Storage | Common CADC path/name | Lifetime | Shared? |
| --- | --- | --- | --- |
| **Scratch** | `/scratch` | Session | **No** |
| **Personal POSIX** | `/arc/home/<user>` | Deployment-managed | Your Sessions |
| **Project POSIX** | `/arc/projects/<group>` | Project allocation | **Yes** (group) |
| **VOSpace service** | `arc:`, `vault:`, or legacy `vos:` | Service policy | VOSpace ACLs |

The Skaha chart calls the shared POSIX service Cavern and defaults to
`/cavern/home` and `/cavern/projects`; CADC deploys it as ARC at `/arc`. Do not
assume either path on another site. Quotas are deployment/allocation values—run
`df -h` on the actual mount or use the site's storage UI.

## Decision guide

```text
Teammate needs live access?     → persistent project POSIX storage
Large temp I/O this session?    → /scratch
Config, certs, small dotfiles?  → persistent personal home (keep small)
Long-term/share/publish?        → a suitable VOSpace service
```

## Session workflow

CADC example (substitute the site's persistent project mount):

```bash
cp /arc/projects/mygroup/raw/big.fits /scratch/
python analyze.py /scratch/big.fits
cp results.csv /arc/projects/mygroup/results/
```

**Scratch is wiped** when the session ends.

## Suggested project layout

```text
/arc/projects/<group>/
├── raw/          # incoming data
├── working/      # intermediate
├── results/      # outputs
├── scripts/      # code
└── docs/         # README, procedures
```

For a non-CADC site, substitute the persistent root shown by that deployment.

## Storage Identifiers

The CLI/API addresses configured VOSpace Services independently of mount paths:

```bash
canfar auth show
canfar data ls -lh arc:/home/$USER
canfar data cp local:/absolute/path/file.fits arc:/projects/mygroup/file.fits
```

CADC commonly discovers `arc` and `vault`; SRCNet prefers a `cavern` service.
Sites may publish other globally unique Storage Identifiers.

## External access

CADC offers SSH/SSHFS access to ARC; other deployments may not. Follow the
site-specific endpoint and key instructions rather than assuming the CADC host.
Details: [Filesystem access](https://www.opencadc.org/canfar/latest/platform/storage/filesystem/)

## Commands

CADC paths:

```bash
df -h /arc/home/$USER
df -h /arc/projects/mygroup
du -sh /arc/projects/mygroup/* | sort -h
```

On CADC, quota/allocation requests go to `support@canfar.net`; other sites use
their own operator or project process. See `canfar-quotas`.

Related: `canfar-transfers`, `canfar-vospace`, `canfar-groups`
