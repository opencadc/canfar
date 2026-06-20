# Repository Instructions

- Always use conventional commit standard for creating commit messages.
- Prefer `rg` and `rg --files` for code search.
- Use `uv` for project commands.
- Keep docs truthful to implemented behavior. Do not document CLI commands, flags, or Python surfaces that do not exist.
- Treat full integration tests as CANFAR-auth-dependent. They require a valid CANFAR account and X.509 certificate/config.

## Repo Map

- `canfar/models/` contains Pydantic models for persisted config, auth contexts, server metadata, registry data, and session request/response shapes.
- `canfar/client.py` owns HTTP client composition, credential precedence, auth hooks, timeouts, and sync/async `httpx` clients. Runtime `token`/`certificate` precedence applies to httpx hook wiring too, not only headers and SSL.
- `canfar/sessions.py`, `canfar/images.py`, `canfar/context.py`, and `canfar/overview.py` expose library modules for Science Platform operations.
- `canfar/cli/` contains Typer CLI adapters. Keep command output, exit behavior, and library calls aligned.
- `canfar/auth/`, `canfar/hooks/`, and `canfar/utils/` contain auth flows, HTTP/Typer hooks, discovery, display, logging, and request builders.
- `tests/` mirrors source modules. Prefer focused tests near the module changed.
- `docs/` is the MkDocs site. Client and CLI behavior documented here must match current code.

## Validation

- Fast lint: `uv run --no-sync ruff check . --no-cache`
- Type check: `uv run ty check canfar`
- Deterministic non-slow tests: `uv run --no-sync pytest tests -m "not slow" --no-cov -q -o cache_dir=/tmp/canfar-pytest-cache`
- Docs build: `uv run --group docs mkdocs build`
- Full test suite: `uv run --no-sync pytest`

Run the full test suite only when a valid CANFAR auth context and certificate are available. Otherwise use the deterministic non-slow test command.

## Agent skills

### Issue tracker

Issues and PRDs are tracked in Jira for the CADC project on `herzberg.atlassian.net`. Use the `CANFAR` label for canfar work. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the canonical triage status mapping in Jira. See `docs/agents/triage-labels.md`.

### Domain docs

This repo uses root `CONTEXT.md` as the current domain glossary. Specs and decisions are Jira-first, not ADR/RFC-first. See `docs/agents/domain.md`.

## Learned User Preferences

- Use caveman style only when the user explicitly invokes it; otherwise use normal concise style.
- During design grilling, ask one question at a time and converge decisions incrementally.
- During broad refactors, preserve existing tests and avoid API/CLI output regressions unless the user explicitly approves those changes.
- Do not introduce a separate DTO/request model layer; use the domain Pydantic models under `canfar/models/` directly and serialize the same model for `--json` output.
- Prefer Python stdlib utilities and Pydantic built-ins (`model_dump`, `model_dump_json`) over custom serialization or config glue; keep the smallest footprint that preserves behavior.

## Learned Workspace Facts

- Issue tracking for this repo uses Jira on `herzberg.atlassian.net`, CADC project, with `CANFAR` label required for canfar work.
- PRDs/spec work for this repo is tracked in Jira (for example `CADC-15643`), not in GitHub Issues.
- Triage is status-based in Jira: `needs-triage` -> To Do, `needs-info` -> On Hold, `ready-for-agent` -> In Progress, `ready-for-human` -> Review, `wontfix` -> On Hold.
- Domain documentation currently uses root `CONTEXT.md` as the glossary.
- Specs and PRDs are Jira-first; durable agent decision records live under `docs/agents/adrs/`, separate from Jira spec tracking.
- Client configuration stores `servers` and `authentication` as dicts keyed by Server Name and IDP; `Server.name` and credential `idp` may duplicate those keys in nested values; Server Selection and `active` references use server names, not IVOA URIs.
- `Session.create` and `AsyncSession.create` should preserve parity and return `list[str]`, using `[]` on total HTTP/network failure without raising.
- CLI layout is kubectl-style: `canfar auth` (bare runs `show`; canonical subcommand names only, `ls`/`rm`), `canfar server`, and `canfar login` (`canfar auth login` is a deprecated alias; `canfar context` was removed).
- CLI machine output (`--json`/`--yaml`) must be data-only on stdout; the human-mode active-server banner must not precede JSON/YAML payloads; serialize via Pydantic `model_dump(mode="json")` rather than custom redaction helpers.
- Built-in default CADC/CANFAR server metadata lists `x509` only; `oidc` and other auth modes are merged from VOSI capabilities enrichment after discovery/login, not static defaults.
- `canfar ps -q` must print all matching session IDs and apply the same `--all`/running-only status filter as table mode.
- `canfar.helpers.distributed` is documented public API used in user batch scripts, not internal/dead code.
- When `HTTPClient` has runtime `token` or `certificate`, skip saved Authentication Record expiry and OIDC refresh httpx hooks (`uses_runtime_credentials`); saved-config hooks apply only without runtime credentials.
