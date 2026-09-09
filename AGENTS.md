# Repository Instructions

- Always use conventional commit standard for creating commit messages.
- Prefix shell commands with `rtk`; use `rtk proxy` when unfiltered output is needed.
- Prefer `rg` and `rg --files` for code search. Use `uv` for project commands.
- Keep docs truthful to implemented behavior. Check command help and source before documenting CLI options or Python APIs.
- Preserve unrelated working-tree changes. Stage only the files belonging to the requested work.

## Repo Map

- `canfar/models/` contains Pydantic models for persisted config, Authentication Records, server metadata, registry data, and Session requests/responses.
- `canfar/models/config.py` defines `Configuration`; `canfar/config/editor.py` owns validated dotted edits and atomic persistence through `config.editor`.
- `canfar/authentication.py` owns public credential operations and Python `login`/`alogin`; `canfar/auth/` implements X.509 and OIDC flows. Shared OIDC credential initialization lives in `canfar/auth/oidc.py`.
- `canfar/server.py` owns public Server Selection and discovery operations; `canfar/_server_discovery.py` implements discovery and metadata enrichment. Selection policy does not live on `Configuration`.
- `canfar/client.py` composes native sync/async `httpx` clients, credentials, auth hooks, and timeouts. Runtime credential precedence applies to hooks as well as headers and TLS.
- `canfar/sessions.py`, `canfar/images.py`, `canfar/context.py`, and `canfar/overview.py` expose Science Platform operations.
- `canfar/storage.py` resolves configured Storage Identifiers into fsspec filesystems; `canfar/cli/data.py` integrates the delegated storage CLI.
- `canfar/cli/` contains Typer adapters. `machine.py` declares leaf output options; `output.py` renders structured output.
- `canfar/hooks/` and `canfar/utils/` contain HTTP/Typer hooks, discovery utilities, logging, and request builders.
- `tests/` mirrors source modules; `tests/conftest.py` isolates the test home and CANFAR environment.
- `docs/` is the MkDocs site; `mkdocs.yml` defines navigation. `skills/canfar/SKILL.md` is the user-facing operations skill, separate from repository engineering guidance.

## Validation

Use these project commands with the `rtk` prefix. Set `UV_CACHE_DIR=/tmp/canfar-uv-cache` if the default cache is unavailable.

- Fast lint: `rtk proxy uv run --no-sync ruff check . --no-cache`
- Type check: `rtk proxy uv run --no-sync ty check canfar`
- Deterministic non-slow tests: `rtk proxy uv run --no-sync pytest tests -m "not slow" --no-cov -q -o cache_dir=/tmp/canfar-pytest-cache`
- Docs build: `rtk proxy uv run --group docs mkdocs build`
- Full test suite: `rtk proxy uv run --no-sync pytest`

Run focused tests for changed behavior before broader validation. Use the deterministic suite for work without live credentials. The full suite contacts CANFAR and creates/deletes test Sessions; run it only with a valid account, usable Authentication Record, and certificate.

Pytest creates an empty temporary home by default, so a certificate in your normal home alone does not configure integration tests. For an authenticated run, set `CANFAR_TEST_HOME` to a prepared temporary home containing a private copy of the test configuration and certificate. Keep the developer's normal configuration untouched and remove the temporary credential copies afterward.

Tests constructing `Configuration` must isolate `CONFIG_PATH`, even when using `model_validate`: settings sources can merge a populated configuration into explicit input. Report deterministic results separately from live service failures; a docs build or local test pass does not establish live workflow success.

## Agent skills

### Issue tracker

Issues, PRDs, and implementation decisions can be tracked in Jira on `herzberg.atlassian.net` (project `CADC`, label `CANFAR`) or GitHub Issues in `opencadc/canfar`. Follow the user's choice or the existing work item's tracker; ask which to use when neither resolves the destination. See `docs/agents/issue-tracker.md`.

### Triage labels

Map the five canonical skill roles to Jira statuses or GitHub issue labels according to the work item's tracker. Keep the `CANFAR` label on Jira work. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: root `CONTEXT.md` is the domain glossary. Read relevant existing records under `docs/agents/adrs/`; the selected Jira or GitHub work item holds the authoritative spec and decisions for that work. See `docs/agents/domain.md`.

## Working Preferences

- Use normal concise prose; use caveman style only when explicitly requested.
- During design grilling, ask one question at a time and converge decisions incrementally. Reuse established tracker and domain choices when rerunning setup.
- During refactors, preserve existing tests and API/CLI output behavior unless a change is explicitly approved.
- Use domain Pydantic models under `canfar/models/` directly; do not introduce a separate DTO/request-model layer. Use those models for structured output where applicable.
- Prefer Python stdlib utilities and Pydantic built-ins (`logging`, `model_dump`, `model_dump_json`, `SecretStr`, `to_jsonable_python`) over custom serialization, configuration glue, or telemetry stacks. Preserve CLI `--log-file` behavior.
- Prefer deleting unused code and dependencies over adding abstraction layers. Keep the supported native sync and async interfaces and distributed helpers.
- Prefer functional tests at public seams (`CliRunner`, `httpx.MockTransport`) over large Authlib-mock matrices or near-duplicate unit cases.

## Current Interface Contracts

- `Configuration.servers` and `.authentication` are dicts keyed by Server Name and IDP. Nested `Server.name` and credential `idp` may repeat those keys. Active and remembered Server Selections reference Server Names; `server.use()` also accepts an IVOA URI as a selector.
- Use `config.editor.get()`, `.set()`, and `.save()` for configuration edits. Use `canfar.authentication` and `canfar.server` operations for credential and server decisions.
- Python `canfar.login()` / `canfar.alogin()` save credentials and discovered servers without selecting the active identity/server. Follow with `authentication.use()`, `server.list_servers()`, and `server.use()` as needed. In a running event loop, use `await alogin()` and offload synchronous selection/discovery with `asyncio.to_thread`; see `docs/client/get-started.md`.
- `Session.create()` and `AsyncSession.create()` return `list[str]`, omit replicas that fail with HTTP/network errors, and return `[]` on total HTTP/network failure. Request validation errors still raise. `destroy_with()` has keyword-only `kind` and `status` filters in both clients.
- Session creation does not imply readiness. Monitor the returned IDs, save results in persistent storage, and scope cleanup to the requested work. Closing a Python client does not delete remote Sessions.
- CLI layout is `canfar login`, `canfar auth`, and `canfar server`. Bare `auth` runs `show`; canonical subcommands include `ls` and `rm`. `canfar auth login` remains a deprecated alias; `canfar context` was removed.
- CLI machine output is leaf `-o json` / `-o yaml` (or `--output`), replacing `--json` / `--yaml`. Supported leaves are bare `auth`, `auth show`, `auth ls`, `server ls`, `create`, `ps`, `config show`, and `config get`. Stdout must contain only the payload; logs and diagnostics go to stderr. Do not add a human server banner or custom redaction/serialization layer.
- `canfar ps` defaults to Pending and Running Sessions; use `--all` for other statuses. `ps -q` applies the same filters and can include the human banner, so use supported machine output for scripts. Quote `canfar prune` prefixes containing shell metacharacters and pass cleanup filters explicitly.
- Built-in CADC/CANFAR server metadata lists `x509` only. Discovery enriches supported authentication modes from VOSI capabilities; do not add OIDC to static defaults without evidence.
- Runtime `HTTPClient` tokens or certificates bypass saved Authentication Record expiry and OIDC refresh hooks (`uses_runtime_credentials`), without changing saved credentials.
- Observability uses stdlib `logging`, Rich stderr, and an optional rotating JSON Lines file via `--log-file`. There is no Logfire or `canfar/utils/telemetry.py` layer. SecretStr masking does not make arbitrary debug response bodies safe to share.
- `canfar data` is a thin POSIX-shaped CLI over configured Storage Identifiers, plus reserved `local`. Python storage access is `canfar.storage.identifiers()` / `filesystem(identifier)`; do not recreate VOSpace functionality in CANFAR or expose dynamic identifier imports.
- Remote storage uses its owning server's IDP independently of the active compute selection. Default `arc` and `vault` require CADC credentials even when compute uses SRCNet. Recursive removal and cross-source `mv` are unsupported; copy and verify before separately scoped removal.

## Documentation and Presentations

- Write for astronomers, advanced programmers, and coding agents. Address readers as "you", explain acronyms on first use, use descriptive headings, and keep paragraphs focused.
- Keep browser workflows complete and client installation optional for them. Compare user-facing feature coverage with both main and the previous published client release when revising the corpus.
- Mark unreleased interfaces explicitly and verify installed capabilities as well as version strings. Keep platform release history separate from client upgrade guidance.
- Update source docstrings as well as Markdown when correcting generated API reference content. Keep the CANFAR operations skill aligned with supported commands and Python APIs.
- Version-control presentation `.typ` source. Generate PDF/PNG previews outside the repository; do not add HTML exports or generated presentation files unless requested.
- `docs/agents/research/` and `docs/agents/reviews/` hold dated evidence. Consult current source and the configured issue tracker before relying on their implementation or release claims.
