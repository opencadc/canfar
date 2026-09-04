---
name: canfar-architecture
description: >
  CANFAR platform architecture: Science Portal, Skaha session manager,
  Kubernetes, Container Registry, Authentication, groups and permissions,
  POSIX storage, VOSpace, scratch, batch, and the OpenCADC repository/deployment
  map. Use when explaining how CANFAR works, what Skaha/Cavern/ARC mean, which
  OpenCADC repository implements a capability, or why deployments differ.
---
# CANFAR architecture

Docs: [Platform overview](https://www.opencadc.org/canfar/latest/)

Start with the user-visible path. Add implementation detail only to explain a
behavior, diagnose a failure, or answer an architecture/deployment question.

## Core components

| Name | Role |
| --- | --- |
| **Science Portal** | Current web UI and browser authentication/session workflow |
| **Skaha** | REST service that lists images and creates/manages Sessions as Kubernetes Jobs |
| **Container Registry** | Publishes allowed Container Images; CADC currently uses Harbor |
| **Authentication** | CADC X.509 or SRCNet OIDC in the current client |
| **IVOA Registry** | Discovers Science Platform Servers and VOSpace Services |
| **GMS / Permissions API** | Deployment-selected authorization for platform access and groups |
| **POSIX Mapper** | Maps authenticated users/groups to UID/GID inside Sessions |
| **Cavern / ARC** | VOSpace service backed by a shared POSIX filesystem |
| **Vault** | CADC VOSpace service used for long-term/publication workflows |

## Request flow

```text
User → Science Portal / canfar CLI
    → Authentication (canfar-auth) — CADC X.509 or SRCNet OIDC
    → IVOA Registry discovery + Server Selection
    → Skaha schedules K8s pod
    → Container from an allowed registry host
    → POSIX Mapper supplies user/group IDs
    → Mounts: deployment persistent root, /scratch, optionally /cvmfs
    → VOSpace APIs expose configured Storage Identifiers
```

## Session types (Skaha)

| Type | Examples | Interactive |
| --- | --- | --- |
| **Notebook** | JupyterLab | Yes |
| **Desktop** | Linux GUI, CASA | Yes |
| **CARTA / Firefly** | Domain viewers | Yes |
| **Contributed** | Community web apps | Yes |
| **Headless / Batch** | Parallel replicas | No |

Detail: `canfar-sessions`, `canfar-batch`.

## Storage tiers

| Tier | Path | Backing | Shared? |
| --- | --- | --- | --- |
| Scratch | Usually `/scratch` | Kubernetes ephemeral storage | No (session) |
| Personal | `/arc/home/<user>` at CADC | Shared POSIX service | Your sessions |
| Projects | `/arc/projects/<group>` at CADC | Shared POSIX allocation | Group |
| VOSpace | `arc:`, `vault:`, `cavern:`, or legacy `vos:` | Service-specific | ACL-based |
| CVMFS | `/cvmfs/soft.computecanada.ca` | Read-only software | When cluster mounts it |

The Skaha chart defaults the persistent root to `/cavern`; CADC's deployment
uses `/arc`. Scratch is ephemeral. Persistent POSIX storage is for active work.
VOSpace capabilities, durability, public access, and quota depend on the service.

## Tooling layers

| Tool | Scope |
| --- | --- |
| `canfar` | Platform: auth, sessions, data staging |
| `canfar data` / Python `canfar.storage` | Current Storage Identifier and fsspec workflow |
| `vcp` / `vls` | Legacy CADC VOSpace I/O |
| `cadcget` / TAP | CADC **archives** (not your vos space) |

Do not conflate `canfar ps` (all your sessions) with in-session monitors.

## OpenCADC implementation map

For repository ownership, current versus legacy components, and which source is
authoritative for a claim, read
[references/ecosystem.md](references/ecosystem.md).

Key boundary: `science-portal` is the current Session web UI;
`canfar-portal` is the public CANFAR website/landing page. The `deployments`
repository contains current supporting charts plus archived copies of older
Skaha and Science Portal charts; current Skaha behavior lives in
`science-platform`.

## Defaults versus a live deployment

- `science-platform/helm/values.yaml` describes chart defaults, such as a
  4-day interactive expiry, five active interactive Sessions, and a 200 GiB
  non-desktop ephemeral-storage ceiling.
- Skaha's headless Job template currently uses a 14-day deadline.
- Operators can override mounts, registries, authorization, quotas, queues,
  resources, and service endpoints. The Portal and client expose the live result.

Use defaults to explain architecture, never to promise capacity to a user.

## Agent rules

1. Check behavior in current code; link the
   [public user guide](https://www.opencadc.org/canfar/latest/) for orientation.
2. Collaboration = **groups + project allocations**, not shared scratch.
3. Archives (CFHT, Gemini, …) ≠ user VOSpace — route to `canfar-cadc-data`.
4. A repository or Helm default is implementation evidence, not live-site evidence.
