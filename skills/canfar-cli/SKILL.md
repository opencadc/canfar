---
name: canfar-cli
description: >
  canfar CLI: login, Authentication and Server Selection, image discovery,
  create/delete/inspect Sessions, platform stats, and data operations with
  Storage Identifiers. Use when driving CANFAR from a terminal or scripting;
  use the Science Portal path for browser-first users.
---
# CANFAR CLI

Docs: [www.opencadc.org/canfar](https://www.opencadc.org/canfar/latest/)

Platform images often include it; locally install with `pip install canfar`.

## Authentication and Server Selection

```bash
canfar login
canfar login cadc
canfar login srcnet
canfar auth show
canfar auth ls
canfar server ls
canfar server use <server-name-or-ivoa-uri>
canfar auth rm cadc          # remove one Authentication record
canfar auth purge --force    # reset all Authentication/Server state
```

Configuration lives at `~/.canfar/config.yaml`. It persists across Sessions only
when the deployment mounts a persistent home there (CADC does). There is no
`canfar logout`; use `auth rm` or `auth purge`.

See `canfar-auth` for Identity Providers, certificates, and discovery.

## Sessions and images

```bash
canfar image ls --kind notebook
canfar create notebook skaha/astroml:latest
canfar create notebook skaha/astroml:latest --name analysis --cpu 4 --memory 16
canfar ps
canfar ps --json
canfar open <session-id>
canfar info <session-id>
canfar events <session-id>
canfar logs <session-id>
canfar stats
canfar delete <session-id>
```

`canfar stats` reports platform capacity, not one Session's cgroup or a storage
quota. Use `canfar info` plus in-Session checks for those.

Session kinds: `canfar-sessions`. Headless jobs: `canfar-batch`.

## Data operations

Operands use **Storage Identifier + absolute service path**. Bare `/arc/...`, an
`active:` alias, and a `canfar storage` command are not supported.

```bash
canfar data ls -lh arc:/home/$USER
canfar data cp local:/absolute/path/file.fits arc:/projects/mygroup/file.fits
canfar data cp vault:/folder/file.fits arc:/home/$USER/file.fits
```

Identifiers come from VOSpace Services discovered for configured Servers. CADC
normally exposes `arc` and `vault`; another deployment may expose `cavern` or a
site-defined name.

Cross-source `mv` and recursive `rm` are intentionally unsupported. Copy, verify
the destination, and perform a separate authorized removal when needed.

Inside a Session, use POSIX `cp` between `/scratch` and persistent storage. For
legacy `vcp`/`vls`, see `canfar-vospace`.

## Automation

```bash
canfar auth show --json
canfar ps --json
```

Machine-output lists have no ordering guarantee. Select by stable Server URI,
Session ID, Storage Identifier, or another explicit field.

## Tool boundaries

| Tool | Scope |
| --- | --- |
| `canfar` | Authentication, Server Selection, Sessions, images, VOSpace data |
| `vcp` / Python `vos` | Legacy CADC VOSpace workflows |
| `cadcget` / `cadctap` | CADC archives and TAP services |

## Agent rules

1. Prefer `canfar ps` over guessing Session IDs from URLs.
2. A laptop can use the client/data API but does not have Session mount paths.
3. Before `delete`, confirm the exact Session ID and whether scratch-only data matters.
