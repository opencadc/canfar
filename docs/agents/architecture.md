# Agent Architecture Notes

Use these notes as navigation guardrails. They are not a refactor backlog.

## Module Map

- Domain request/response and config shapes live in `canfar/models/`.
- HTTP composition, credential precedence, sync/async clients, and auth hooks live in `canfar/client.py`.
- User-facing library operations live in `canfar/sessions.py`, `canfar/images.py`, `canfar/context.py`, and `canfar/overview.py`.
- Typer command adapters live in `canfar/cli/` and should stay thin over library modules.
- Auth flows live in `canfar/auth/`; request/response hooks live in `canfar/hooks/`.
- Discovery, display, logging, request builders, and other helper modules live in `canfar/utils/`.

## Current Seams

- `Configuration` is the persistent config seam. Tests that construct it must isolate `CONFIG_PATH` from the developer's real `~/.canfar/config.yaml`.
- `HTTPClient` is the transport seam. It decides runtime credential precedence before creating `httpx` clients.
- `Session` and `AsyncSession` duplicate many operations in sync/async form. Keep behavior aligned when changing either adapter.
- CLI modules are adapters over library modules. Prefer testing command parsing/output separately from library behavior.
- Request builders in `canfar/utils/build.py` are useful test surfaces for payload shape and validation.

## Authentication Configuration

Canonical code stores `OIDCCredential` and `X509Credential` Authentication
Records in `Configuration.authentication` and accesses them through
`Configuration.get_credential`, `upsert_credential`, and `update_credential`.
`ActiveConfig` owns the active Authentication and Server Selection references;
`HTTPClient` composes `Configuration` and resolves those records for transport.

The legacy `OIDC` and `X509` models, `Configuration.context` and `.contexts`,
and the selection compatibility shims remain working compatibility views. New
code should use the canonical records and `Configuration` methods directly.

## Test Caveats

- Some tests touch live CANFAR endpoints even if they are not long-running. They must be marked `slow` and `integration`.
- `pytest -m "not slow"` should be deterministic without real CANFAR credentials.
- Full `uv run --no-sync pytest` requires valid CANFAR auth and may depend on platform availability.

## Change Rules

- Match CLI behavior to docs and docs to CLI behavior in the same change.
- Avoid new seams until at least two adapters need them.
- Prefer Pydantic models for structured request/config data instead of ad hoc dict handling at call sites.
- Keep secret-bearing config output redacted or explicitly justified.
