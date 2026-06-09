# Repository Instructions

- Always use conventional commit standard for creating commit messages.
- Prefer `rg` and `rg --files` for code search.
- Use `uv` for project commands.
- Keep docs truthful to implemented behavior. Do not document CLI commands, flags, or Python surfaces that do not exist.
- Treat full integration tests as CANFAR-auth-dependent. They require a valid CANFAR account and X.509 certificate/config.

## Repo Map

- `canfar/models/` contains Pydantic models for persisted config, auth contexts, server metadata, registry data, and session request/response shapes.
- `canfar/client.py` owns HTTP client composition, credential precedence, auth hooks, timeouts, and sync/async `httpx` clients.
- `canfar/sessions.py`, `canfar/images.py`, `canfar/context.py`, and `canfar/overview.py` expose library modules for Science Platform operations.
- `canfar/cli/` contains Typer CLI adapters. Keep command output, exit behavior, and library calls aligned.
- `canfar/auth/`, `canfar/hooks/`, and `canfar/utils/` contain auth flows, HTTP/Typer hooks, discovery, display, logging, and request builders.
- `tests/` mirrors source modules. Prefer focused tests near the module changed.
- `docs/` is the MkDocs site. Client and CLI behavior documented here must match current code.

## Validation

- Fast lint: `uv run --no-sync ruff check . --no-cache`
- Type check: `uv run --no-sync mypy canfar --config-file pyproject.toml`
- Deterministic non-slow tests: `env HOME=/private/tmp/canfar-empty-home uv run --no-sync pytest tests -m "not slow" --no-cov -q -o cache_dir=/tmp/canfar-pytest-cache`
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

## Learned Workspace Facts

- Issue tracking for this repo uses Jira on `herzberg.atlassian.net`, CADC project, with `CANFAR` label required for canfar work.
- PRDs/spec work for this repo is tracked in Jira (for example `CADC-15643`), not in GitHub Issues.
- Triage is status-based in Jira: `needs-triage` -> To Do, `needs-info` -> On Hold, `ready-for-agent` -> In Progress, `ready-for-human` -> Review, `wontfix` -> On Hold.
- Domain documentation currently uses root `CONTEXT.md` as the glossary.
- Specs/decisions are Jira-first; this repo does not keep ADR/RFC directories as the source of truth.
- `Session.create` and `AsyncSession.create` should preserve parity and return `list[str]`, using `[]` on total HTTP/network failure without raising.
- CLI layout is kubectl-style across domain seams: `canfar auth` (Authentication), `canfar server` (Platform), and `canfar login`.
- `canfar login` is the supported login entrypoint; `canfar auth login` is a deprecated compatibility alias.
- `canfar context` was removed; use `canfar auth show`, `canfar auth ls`, and `canfar server ls` for combined auth/server state.
- Bare `canfar auth` runs `show`; supported subcommand names are canonical only (`ls`/`rm`, not `list`/`remove` aliases).
- CLI machine output (`--json`/`--yaml`) must be data-only on stdout; the human-mode active-server banner must not precede JSON/YAML payloads.
- Built-in default CADC/CANFAR server metadata lists `x509` only; `oidc` and other auth modes are merged from VOSI capabilities enrichment after discovery/login, not static defaults.
