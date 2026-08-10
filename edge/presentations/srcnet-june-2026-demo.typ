#import "@preview/diatypst:0.9.3": *

#show: slides.with(
  title: "Team CORAL Demo",
  subtitle: "CANFAR CLI v1.4+",
  date: "June 2026",
  authors: "Shiny Brar · CADC",
  footer-subtitle: "canfar 1.4",
  ratio: 16 / 9,
  layout: "medium",
  title-color: rgb("#ed7869"),
  count: "number",
  toc: false,
)

== Why you should care

Ubiquitous *front door* to the CANFAR Science Platform.

- *One command* logs you in, discovers Servers, and picks one
- *Multi-identity:* CADC and SRCNet — switch hats without re-wiring
- *Same flow everywhere* — shell, scripts, and notebooks
- *Machine-readable* output → automation- and pipeline-ready

= The Authentication Inversion

== Before #sym.arrow.r After

#grid(
  columns: (1fr, 1fr),
  column-gutter: 1.2em,
  [
    *Before — server-first* (≤ 1.3.5)
    ```bash
    canfar auth login   # deprecated
    canfar context      # removed
    ```
    - Auth bound to a Server / context up front
    - Switching meant re-wiring config
  ],
  [
    *Now — identity-first* (1.4)
    ```bash
    canfar login srcnet
    canfar server use canSRC
    ```
    - Pick identity once; Servers discovered for you
    - Last Server per IDP is remembered
  ],
)

#align(center)[_Tell it who you are, not where to stand._]

== Live: same command, any SRC node

```bash
canfar server use sweSRC
canfar create headless skaha/base-notebook:latest -- env
canfar logs $(canfar ps -a --json | jq -r ".[0].id")

canfar server use canSRC
canfar create headless skaha/base-notebook:latest -- env
canfar logs $(canfar ps -a --json | jq -r ".[0].id")
```

- Pick a node, browse images, launch a headless session, read its logs
- *Same `create` command* on `canSRC` — workloads are portable across nodes
- One identity, every node — hop with `canfar server use`

= Built for scripts & scale

== Machine output you can pipe

```bash
canfar config get active.server --json
canfar open $(canfar ps --json | jq -r ".[0].id")
```

- `--json` / `--yaml` on `auth`, `server`, `ps`, `config`
- Data on *stdout*, diagnostics on *stderr* → safe to pipe

The same flow at package level, for notebooks and pipelines:

```python
from canfar import login, server, sessions
login("srcnet")
for node in ["canSRC", "sweSRC"]:
    server.use(node)
    session = sessions.AsyncSession()
    await session.create(image="skaha/base-notebook:latest", cmd="env")
```

== Data, same front door

File management over named VOSpace Services, using their configured Authentication Records:

```bash
canfar data ls -lh canSRC:/
canfar data cp local:/absolute/path/filename canSRC:/data/filename
```

- Cross-source movement is explicit `cp`, verify, then separate `rm`
- Each VOSpace Service uses its parent Science Platform Server's IDP
- CANFAR uses that IDP's saved Authentication Record, even when the Science Platform Server is inactive

#align(center)[_Your files, your compute, your platform — one door, one login._]
