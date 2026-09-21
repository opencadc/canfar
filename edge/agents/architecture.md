# Agent Architecture Notes

Use these notes as navigation guardrails. They are not a refactor backlog.

## Module Map

- Domain request/response and config shapes live in `canfar/models/`.
- HTTP composition, credential precedence, sync/async clients, and auth hooks live in `canfar/client.py`.
- User-facing library operations live in `canfar/sessions.py`, `canfar/images.py`, `canfar/context.py`, and `canfar/overview.py`.
- Typer command adapters live in `canfar/cli/` and should stay thin over library modules.
- Auth flows live in `canfar/auth/`; request/response hooks live in `canfar/hooks/`.
- Discovery, logging, request builders, and other helper modules live in `canfar/utils/`.

## Current Seams

- `Configuration` is the validated persisted data seam; `config.editor` owns dotted edits and atomic saves. Tests that construct it must isolate `CONFIG_PATH` from the developer's real `~/.canfar/config.yaml`.
- `HTTPClient` is the transport seam. It decides runtime credential precedence before creating `httpx` clients.
- `Session` and `AsyncSession` duplicate many operations in sync/async form. Keep behavior aligned when changing either adapter.
- CLI modules are adapters over library modules. Prefer testing command parsing/output separately from library behavior.
- Request builders in `canfar/utils/build.py` are useful test surfaces for payload shape and validation.
- Logging is stdlib `logging` plus Rich stderr and optional `--log-file` JSONL (`canfar/utils/logging.py`). There is no Logfire, OTLP, or `telemetry.py` layer.

## Authentication Configuration

`OIDCCredential` and `X509Credential` Authentication Records live in
`Configuration.authentication`. The bound `config.editor` owns validated edits
and atomic persistence; Authentication and Platform operations own decisions
about credentials, servers, and Server Selection. `ActiveConfig` stores the
active Authentication and Server Selection references; `HTTPClient` composes
`Configuration` and resolves those records for transport. Server Selection
history lives on `ActiveConfig` and the Platform operation (there is no separate
`selection.py` shim).

## Test Caveats

- Some tests touch live CANFAR endpoints even if they are not long-running. They must be marked `slow` and `integration`.
- `pytest -m "not slow"` should be deterministic without real CANFAR credentials.
- Full `uv run --no-sync pytest` requires valid CANFAR auth and may depend on platform availability.

## Change Rules

- Match CLI behavior to docs and docs to CLI behavior in the same change.
- Avoid new seams until at least two adapters need them.
- Prefer Pydantic models for structured request/config data instead of ad hoc dict handling at call sites.
- Keep secret-bearing config output redacted or explicitly justified.

## Platform repositories

The client talks to services maintained in other `opencadc` repositories.
Checked on 2026-09-18:

| Component | Repository | Notes |
| --- | --- | --- |
| Session service (skaha) | `opencadc/science-platform` (`skaha/`, chart in `helm/`) | Launch templates in `helm/skaha-config/launch-*.yaml` define each Session Kind's ports, probes, and limits |
| Science Portal | `opencadc/science-portal` | `opencadc/canfar-portal` is the static canfar.net website |
| Persistent storage (Cavern) | `opencadc/vos` (`cavern/`) | Chart in `opencadc/deployments` |
| Object storage (Vault) | `opencadc/storage-inventory` (`vault/`) | |
| Users, groups, POSIX mapping | `opencadc/ac` (`ac/`, `posix-mapper/`) | The SRCNet permissions service is external |
| Service registry | `opencadc/reg` | |
| Storage Management UI | `opencadc/storage-ui` | |
| Container Registry | External Harbor instance | The Session service caches its artifact labels |
| Legacy CLI tools | `opencadc/vostools`, `opencadc/cadctools` | `vos`, `cadcdata`, `cadctap`, `cadcutils` on PyPI |

When the docs state a Server default, cite the chart value or template line it
came from, and present it as a default an operator can change.

## Historical notes

Files under `docs/agents/research/` and `docs/agents/reviews/` are dated
snapshots from audits and research. Prefer this file and `docs/cli/` for
current design; treat older notes as historical unless they match the code.
