---
name: canfar-permissions
description: >
  CANFAR permissions beyond groups: platform authorization, project allocations,
  POSIX ownership/modes, VOSpace ACLs, Container Registry roles, API
  Authentication, and external collaborators. Use when access is denied or the
  user asks about chmod, registry access, allocation, or ACLs.
---
# Permissions & access control

Treat these as separate gates:

```text
Authentication → platform entitlement → group membership → project allocation
               → POSIX mode/ownership or VOSpace ACL → registry role
```

**Groups (primary):** see `canfar-groups` for membership admin.

Docs: [Permissions](https://www.opencadc.org/canfar/latest/platform/permissions/)

Skaha deployments can authorize Session creation through an IVOA GMS group or a
Permissions API. That platform entitlement is separate from data access.

## Project allocations

A project directory (CADC example `/arc/projects/<name>`) is a managed allocation
with quota, group mapping, and filesystem ownership:

- **Not** created with `mkdir`
- Request through the site's allocation process (CADC: `support@canfar.net`)
- PI/group admin ties allocation to CADC group

## POSIX persistent storage

CADC example:

```bash
ls -la /arc/projects/mygroup/
chmod 664 shared.fits
chmod 755 scripts/run_pipeline.sh
chgrp mygroup shared.fits    # when group ownership needed
```

Run `id`, `ls -ld`, and `namei -l <path>` before changing modes. Do not make a
directory world-writable to bypass missing membership or allocation.

## VOSpace ACLs

VOSpace ACLs are service metadata and are not identical to POSIX modes. At CADC,
use Storage UI Properties or the exact `vchmod` group syntax.
Public release: explicit **other-read** on Vault — see `canfar-vospace`.

## Harbor (containers)

- **Pull** policy depends on repository visibility and Skaha's allowed registry hosts
- **Push** requires a role in that Container Registry project
- Team images: grant group access to Harbor project

## API / automation

Same CADC identity for CLI, Python client, and archives.
Tokens/certs — `canfar-auth`.

## Headless identity

Batch and headless jobs run as **your** identity — input paths on persistent
project storage (CADC: `/arc/projects`) must be readable by you (and the group
if workers share group context).

## Agent rules

1. Permission denied → **group membership** first, not `sudo`.
2. Public data → **Vault** with explicit ACLs; ARC projects stay private by default.
3. External partners → PI adds to **group**, not ad-hoc world-readable home dirs.

Related: `canfar-groups`, `canfar-auth`
