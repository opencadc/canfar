---
name: canfar-sessions
description: >
  CANFAR interactive sessions: Notebook JupyterLab, Desktop GUI, CARTA radio,
  Firefly tables, Contributed apps, headless batch, flexible vs fixed resources,
  GPU, Session lifecycle, Science Portal and canfar create. Use when launching
  sessions, choosing session type, CARTA Firefly desktop notebook.
---
# Interactive sessions

Docs: [Sessions overview](https://www.opencadc.org/canfar/latest/platform/sessions/)

For a simple user, give the Science Portal path first: log in, choose a Session
kind, select one of the images actually shown for that kind, name it, and launch.
Use the CLI/API path for repeatability, batch work, or troubleshooting.

## Session types

| Type | Interface | Best for |
| --- | --- | --- |
| **Notebook** | JupyterLab | Analysis, teaching, prototyping |
| **Desktop** | Full Linux GUI | CASA, legacy GUI tools |
| **CARTA** | Radio astronomy viewer | Cubes, masks, regions |
| **Firefly** | Table/image viewer | Survey catalogs |
| **Contributed** | Community web apps | marimo, VS Code web, custom |
| **Headless** | No UI | Batch — see `canfar-batch` |

Available kinds and images come from the live Skaha service; not every deployment
offers every row. Discover with the Portal or `canfar image ls`.

## Lifecycle

- **Start:** scheduling and image pulls can take seconds to minutes.
- **Runtime:** deployment-configured. The current chart defaults interactive
  Sessions to 4 days, but a live site may override it. Check the Portal or
  `canfar info <session-id>` for the actual expiry. The current headless Job
  template has a separate 14-day deadline.
- **End:** container deleted — data copied to the site's persistent POSIX storage
  or VOSpace remains subject to that service's policy

Always persist to the site's shared POSIX mount or VOSpace before deletion.

## Session count limits

Interactive Sessions (notebook, desktop, CARTA, Firefly, contributed) share a
**per-user cap**. The chart default is five; the live deployment is authoritative.
Headless/batch creates and existing **desktop-app** Sessions (software launched
inside a Desktop — not the Desktop session itself) are exempt from this
particular Skaha check. Desktop sessions still count toward the cap.
At cap, **new creates are rejected** — delete idle sessions:

```bash
canfar ps
canfar delete <session-id>
```

## Resources

| Mode | When |
| --- | --- |
| **Flexible** (default) | Exploration and teaching; site policy supplies request/limit |
| **Fixed** (`--cpu`, `--memory`) | Measured workloads needing a specific allocation |

```bash
canfar image ls --kind notebook
canfar create notebook skaha/astroml:latest
canfar create notebook skaha/astroml:latest --cpu 4 --memory 16
```

## GPU

Request GPU only when the Portal/context exposes GPUs and use an image compatible
with that site's GPU stack. Verify with `nvidia-smi` inside the Session.

## Contributed applications

Portal → **Contributed** → pick app. Web UI must listen on **port 5000**
(Skaha probe contract). The service does not itself require
`/skaha/startup.sh` for contributed Sessions; the image's configured command must
start the service. Community guide:
[Contributed apps](https://www.opencadc.org/canfar/latest/platform/sessions/contributed/)

## Agent rules

1. `/scratch` is invisible to other Sessions — not a bug.
2. Match session type to workflow (CARTA for radio cubes, not Notebook alone).
3. Pending after create → `canfar events <id>`, not just "wait" (queue, pull, probe).

Related: `canfar-containers`, `canfar-limits`, `canfar-cli`
