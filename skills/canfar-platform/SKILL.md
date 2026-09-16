---
name: canfar-platform
description: >
  CANFAR Science Platform at CADC, SRCNet, or a compatible Skaha deployment.
  Use for any CANFAR
  question: account access, groups, sessions, scratch vs ARC vs Vault, quotas,
  transfers, permissions, containers, Harbor, Python client, CLI auth, DOI,
  CADC archives, CVMFS, limits, troubleshooting. Users do not name skills —
  read the matching skill below.
---
# CANFAR platform (intent router)

Users describe goals in plain language. **Do not ask them to pick a skill name.**
Read the skill that matches (under `~/.cursor/skills/` when `canfar-platform`
is installed).

## Answer for the user in front of you

- **Student or occasional user:** explain the concept in plain language and give
  the Science Portal path first. Add at most one verification command when useful.
- **Scientist:** make data lifetime, reproducibility, quota, and collaboration
  consequences explicit.
- **Team or PI:** distinguish identity, group membership, project allocation,
  filesystem permissions, and VOSpace sharing; they are related but not identical.
- **Power user:** add current `canfar` CLI or Python API examples and prefer
  machine-readable output for automation.

Do not expose Kubernetes, Helm, or service internals unless the user asks how the
platform works or needs help diagnosing a deployment problem.

## Deployment discovery

Examples use the **CADC** deployment (`www.canfar.net`, `images.canfar.net`).
The open-source charts are configurable and SRCNet sites may expose different
Server Names, Storage Identifiers, registry hosts, mounts, quotas, and limits.
After login, discover instead of guessing:

```bash
canfar auth show
canfar server ls
canfar image ls
canfar ps
```

- **CADC client defaults:** X.509 Authentication, `arc` and `vault` Storage Identifiers
- **SRCNet client defaults:** OIDC Authentication, preferred storage leaf `cavern`
- **Limits:** deployment-configured; inspect the Portal, `canfar info <id>`,
  `canfar stats`, and `canfar events <id>`
- **Support:** CADC uses `support@canfar.net`; other deployments see portal/Discord

Use current code and tests for supported behavior and syntax. Use Helm templates
and the site's deployed values/live output for configured endpoints, paths,
limits, and availability. Treat public documentation as orientation only when it
agrees with the implementation. Never present a chart default as the user's
allocation.

## Route by intent

| User is trying to… | Read skill |
| --- | --- |
| Get account, first steps, acknowledgement | `canfar-getting-started` |
| Platform or OpenCADC implementation overview | `canfar-architecture` |
| Launch/manage sessions, CARTA, Firefly, Desktop | `canfar-sessions` |
| Scratch vs persistent personal/project storage | `canfar-storage` |
| Vault, `vos:`, VOSpace sharing, public data | `canfar-vospace` |
| Move data (SSHFS, rsync, large uploads) | `canfar-transfers` |
| Quotas, disk full, request more space | `canfar-quotas` |
| Create/manage groups, add members | `canfar-groups` |
| ACLs, project allocations, Harbor access | `canfar-permissions` |
| Headless batch, replicas, parallel jobs | `canfar-batch` |
| Docker images, astroml, custom containers | `canfar-containers` |
| `canfar login`, IDP, certificates, servers | `canfar-auth` |
| `canfar create/ps`, CLI automation | `canfar-cli` |
| Python `Session` / `AsyncSession` | `canfar-python-client` |
| Publish data with DOI (DPS) | `canfar-doi` |
| CADC archive download (`cadcget`, etc.) | `canfar-cadc-data` |
| Session CPU/RAM/GPU, cgroup, scratch size | `canfar-limits` |
| Alliance software, `/cvmfs`, `module load` | `canfar-cvmfs` |
| Scale-out pipelines, batch-friendly code | `canfar-best-practices` |
| Shared home/project storage, concurrent sessions | `canfar-concurrency` |
| Failures, pending sessions, lost files | `canfar-troubleshooting` |

If storage + quota both apply: `canfar-storage` then `canfar-quotas`.

## Storage truths

| Concept | Common CADC name | Lifetime | Shared across sessions? |
| --- | --- | --- | --- |
| Session scratch | `/scratch` | Session | **No** |
| Personal persistent storage | `/arc/home/<you>` | Deployment-managed | **Yes** |
| Team persistent storage | `/arc/projects/<group>` | Project allocation | **Yes** (group) |
| VOSpace service | `arc:`, `vault:`, or legacy `vos:` | Service policy | Per VOSpace ACLs |

The Skaha chart calls the persistent POSIX service **Cavern** and defaults its
mount to `/cavern`; CADC deploys the corresponding service as ARC at `/arc`.
Use the site's names and paths rather than translating them blindly.

```bash
canfar ps
canfar auth show
df -h /arc/home/$USER /arc/projects/<group> 2>/dev/null   # CADC; substitute site mounts
```

Public guide (orientation):
[www.opencadc.org/canfar](https://www.opencadc.org/canfar/latest/)

## Install / update

```bash
npx skills add opencadc/canfar
npx skills update   # when available / as needed
```
