---
name: canfar-quotas
description: >
  CANFAR storage quotas and allocation: distinguish personal/project POSIX,
  Session ephemeral storage, and VOSpace; inspect live usage with df/du or site
  UI; request more capacity through the deployment process. Use when disk full,
  quota percent, space left, or no space.
---
# Quotas & disk usage

Docs: [Storage overview](https://www.opencadc.org/canfar/latest/platform/storage/)

## Do not guess the quota

CADC commonly provides a small personal home and separately allocated project
space. The Cavern chart default first-user allocation is 10 GiB (`defaultSizeGB`).
The Skaha chart's 200 GiB non-desktop ephemeral-storage ceiling is a Job-template
default; desktop scratch uses a different template. Operators override these.
Those numbers are implementation defaults, not the user's live allocation — run
`df` or the site UI.

## Check usage (all users)

CADC paths (substitute the site's persistent home/project mount):

```bash
df -h /arc/home/$USER
df -h /arc/projects/mygroup
du -sh /arc/home/$USER/* 2>/dev/null | sort -h
du -sh /arc/projects/mygroup/* 2>/dev/null | sort -h
```

Vault: [Vault file manager](https://www.canfar.net/storage/vault/list/) usage display.

## Request more space

For CADC, email **`support@canfar.net`** with:
- Project name
- Current usage / quota
- Requested size
- Brief science justification

For SRCNet or another deployment, use the site's project/allocation process.

## Home quota tips

Keep home for:
- `~/.canfar`, `~/.ssh`, configs, small scripts

**Not** for datasets, large environments, or download caches—use project storage
or Session scratch. Substitute the site's persistent path for `/arc`.

## Scratch

Full scratch ≠ home full. Scratch resets each session — delete temp files freely.

On Ceph-backed homes, directory `rbytes` may lag after large writes — refresh
`df` rather than assuming the quota percent is stale forever.

## Agent rules

1. Run `df`/`du` before delete advice — cite paths and sizes.
2. Warn at >90% home: saves and logins may fail.
3. Big science data → **project allocation**, not personal home.

Related: `canfar-storage`, `canfar-groups` (project allocations)
