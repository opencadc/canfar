---
name: canfar-concurrency
description: >
  CANFAR concurrent Sessions: shared persistent personal/project POSIX storage,
  per-Session scratch, atomic writes and lock-heavy database pitfalls. Use when
  two Sessions write concurrently, files appear inconsistent, or the user asks
  what state is shared.
---
# Concurrency & shared home

## Two sessions, one home

At CADC, every interactive Session mounts the same `/arc/home/<user>`. Other
deployments commonly mount the same persistent home below `/cavern`. Each
Session has its own `/scratch`; use the live mount paths.

| State | Location | Concurrent? |
| --- | --- | --- |
| Config, SSH keys, `~/.canfar` | CADC: `/arc/home` | Read-mostly OK |
| Active datasets | CADC: `/arc/projects/<group>` | Group POSIX — coordinate |
| Temp I/O | `/scratch` | **Per session only** |
| Vault releases | `vos:…` | ACL-controlled |

**Rule:** teammates share via the site's persistent project mount (CADC:
`/arc/projects`) or VOSpace — not `/scratch`.

## Shared POSIX filesystem cautions

- The backing filesystem is deployment-specific. Avoid heavy **SQLite** or
  lock-heavy apps on shared personal storage; use local scratch for active DB
  state and copy durable exports/checkpoints back safely.
- Use atomic writes (write temp + rename) for config files.
- Large parallel writes to one directory can slow everyone — spread outputs.

## Agent rules

1. Two sessions = two scratches; share via the persistent project mount (CADC:
   `/arc/projects`) or `vcp`.
2. Permission denied on a project file → inspect identity, group, allocation, and POSIX mode.
