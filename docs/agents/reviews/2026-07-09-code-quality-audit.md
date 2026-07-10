# CANFAR Overall Code Quality Audit

- **Audit date:** 2026-07-09
- **Snapshot:** `main` at `f6609e23`
- **Scope:** whole repository, read-only code-quality and over-engineering review
- **Review tracks:** thermo-nuclear maintainability review and ponytail whole-repo audit

## Executive verdict

The repository has a healthy executable baseline: lint, type checking, and all
deterministic non-slow tests pass. It is not a spaghetti codebase, and no shipped
Python file has crossed the thermo-nuclear 1,000-line threshold.

The architecture is nevertheless carrying several expensive seams:

- `Session` and `AsyncSession` maintain the same nine operations by copying policy.
- The canonical Authentication Record and Server Selection schema is converted back
  into a legacy context shape inside the HTTP client and auth hooks.
- The persisted Science Platform Server model owns HTTP I/O and fallback policy.
- OIDC protocol code, browser/QR presentation, Rich progress, and model mutation are
  fused into one 512-line module.
- Importing `canfar` can read and reject the user's configuration before the user
  invokes an operation.
- A superseded discovery/display path and heavily duplicated tests contribute a
  large amount of code without supporting the live product path.

The highest-leverage move is not a broad rewrite. It is to delete the dormant path,
make the existing domain seams canonical internally, and share only pure policy
between sync and async adapters.

## Evidence snapshot

| Measure | Current result |
| --- | ---: |
| Shipped Python | 73 files / 10,055 physical lines |
| Test Python | 62 files / 14,759 physical lines |
| Test-to-production ratio | 1.468 |
| Production files at least 1,000 lines | 0 |
| Production files at least 500 lines | 3 |
| Test files at least 1,000 lines | 1 |
| Largest production file | `canfar/sessions.py`, 870 lines |
| Largest test file | `tests/test_helpers_distributed.py`, 1,651 lines |

Largest production files:

1. `canfar/sessions.py` — 870 lines
2. `canfar/server.py` — 514 lines
3. `canfar/auth/oidc.py` — 512 lines
4. `canfar/models/config.py` — 442 lines
5. `canfar/client.py` — 433 lines

Largest function spans:

1. `canfar/cli/create.py:61` `creation` — 159 lines
2. `canfar/cli/ps.py:32` `show` — 128 lines
3. `canfar/utils/vosi.py:123` `capabilities` — 103 lines
4. `canfar/sessions.py:598` async `create` — 97 lines
5. `canfar/auth/oidc.py:344` `_authflow_impl` — 93 lines

The current branch is one docs-only commit ahead of `origin/main`; that commit adds a
Typst demo and does not affect the production-code findings.

## Issue #100 is planned work, not a new audit backlog

[#100 — PRD: Logging Architecture and Observability Vertical Slice](https://github.com/opencadc/canfar/issues/100)
is open and labeled `enhancement`, `PRD`, and `ready-for-agent`. It has no assignee,
milestone, project item, or comments. It was last updated on 2026-05-23.

The following visible debt is already owned by #100 and is deliberately excluded
from the independent findings and deletion estimates below:

- the 249-line `canfar/utils/logging.py` implementation;
- logging configuration and Rich traceback installation at import time;
- the process-wide log-level side effect in `HTTPClient` validation;
- scattered CLI verbosity handling and the future `--log-level` / repeated `-v`
  contract;
- stdout/stderr discipline and structured machine diagnostics;
- redaction, request correlation, and HTTPX instrumentation;
- Logfire/OpenTelemetry configuration and optional OTLP export;
- file sinks, rotation, JSON Lines, fallback behavior, and logging documentation;
- logging-test replacement with externally observable behavior tests.

Do not start a competing stdlib-only logging rewrite. Issue #100 explicitly chooses
Logfire, a big-bang internal migration, and no compatibility shim.

Two implementation cautions should be preserved when #100 is executed:

- `canfar version --debug` means "show bug-report details", not "enable logging".
- `canfar info --debug` both raises verbosity and displays response anomalies; a
  mechanical flag replacement would remove non-logging behavior.

The non-logging console/config import problem described below is adjacent to #100,
but is outside its logging-only scope.

## Combined structural findings

### P1 — Make `import canfar` inert with respect to user configuration

`canfar/utils/console.py:45` constructs a configured Rich console at module import:

```python
console: Console = get_console()
```

`get_console()` constructs `Configuration()`. The eager import path is
`canfar.__init__ -> server -> Discover -> console`, so a stale
`~/.canfar/config.yaml` can make `import canfar` fail. This is not hypothetical:
`tests/test_import_isolation.py:17` currently asserts that failure.

Concrete improvement:

- delete the module-level configured console;
- call `get_console()` from CLI command execution, after configuration migration and
  validation are intentionally in scope;
- remove console output from discovery and OIDC protocol modules;
- reverse the isolation test so importing the library must succeed with stale user
  state.

This makes import behavior predictable without inventing a proxy object or another
configuration layer.

### P1 — Stop converting canonical Authentication state back into legacy contexts

The persisted schema already separates Authentication Records from Science Platform
Servers. Internally, however, `canfar/client.py:239`, `canfar/client.py:274`, and
`canfar/client.py:330` obtain `config.context`, rebuilding legacy `OIDC` or `X509`
objects with an embedded server. `canfar/hooks/httpx/auth.py:87` then writes refreshed
tokens back through `config.contexts`.

That makes the compatibility adapter part of the core runtime and forces maintainers
to reason about two representations of the same Authentication state.

The code-judo move is to keep compatibility at the boundary and make canonical
records the only internal representation:

```python
idp = config.active.authentication
credential = config.get_credential(idp)
server = config.get_active_server()

if isinstance(credential, OIDCCredential):
    updated = credential.model_copy(
        update={
            "token": credential.token.model_copy(update={"access": token}),
            "expiry": credential.expiry.model_copy(update={"access": expiry}),
        }
    )
    config.authentication[idp] = updated
```

Move `valid`/`expired` behavior onto `OIDCCredential` and `X509Credential`, or into
small pure functions over those models. Keep `Configuration.context` and `.contexts`
only as an explicitly deprecated compatibility boundary until a breaking release can
remove them.

Server Selection rules also have two peer APIs today: free functions in
`canfar/config/selection.py` and forwarding methods in
`canfar/models/config.py:270-406`. Pick one internal owner. The low-risk choice is to
use `config.selection` internally and retain model methods only for public
compatibility; if `Configuration` is intended to be the public canonical seam, fold
the implementations into it in one change. Do not keep both forms as peer call paths.

Finally, `canfar/config/store.py:50` writes directly to the target YAML file. Preserve
the existing one-save orchestration, but write a temporary file in the target
directory and finish with `os.replace()` so an interruption cannot leave partial
configuration.

### P1 — Share Session policy, not a magical sync/async transport abstraction

`Session` occupies lines 31-406 of `canfar/sessions.py`; `AsyncSession` repeats the
same nine public operations at lines 409-870. Together the classes occupy 838 of 870
lines (96.3%). Their paired operations span 784 lines.

The async side also repeats the same semaphore / gather / exception-filter loop in
`info`, `logs`, `create`, `events`, and `destroy`. Similar copied policy has already
drifted elsewhere: `canfar/hooks/httpx/auth.py:161` documents that the async refresh
hook intentionally lacks the sync hook's `ctx.valid` guard.

Keep both public adapters. Extract only the behavior that should be identical:

```python
def _ids(value: str | list[str]) -> list[str]:
    return [value] if isinstance(value, str) else value


def _session_name_pattern(prefix: str) -> re.Pattern[str]:
    meta = set(".^$*+?{}[]()|")
    return re.compile(prefix if any(c in meta for c in prefix) else rf"^{re.escape(prefix)}")
```

Likewise, build `CreateRequest` once and pass that model into a shared payload builder.
If the scalar `create(...)` API must remain compatible, keep it as one thin adapter
that constructs `CreateRequest`; do not maintain scalar and model-first
implementations as peers.

Avoid solving this with a generic sync/async transport protocol, decorators, or code
generation. Python's I/O mechanics are genuinely different; ID normalization,
selector compilation, payload generation, refresh eligibility, and result parsing
are the parts that should be shared.

### P1 — Make the Science Platform Server model pure data

`canfar/models/http.py:27` begins as a persisted Pydantic Science Platform Server
model, then owns VOSI retrieval, sync and async HTTP-client construction,
Authentication configuration loading, fallback policy, and context-response parsing
through line 301. Local imports of `HTTPClient` and `Configuration` at lines 179 and
210 are evidence that the ownership direction is backwards.

`Server.afetch()` has no production or documentation caller. `Server.fetch()` has one
production caller in the Platform service.

Move the I/O to `canfar/server.py` (or reuse the existing `canfar.context.Context`
client) and leave model methods for parsing/copying only:

```python
def fetch_server_resources(
    server: Server,
    *,
    config: Configuration,
    timeout: int,
) -> Server:
    base_url = AnyHttpUrl(f"{server.url}/{server.version}")
    resources = Context(
        config=config,
        url=base_url,
        timeout=timeout,
        raise_http_errors=False,
    ).resources()
    return server.model_copy(update=resource_settings(resources), deep=True)
```

This deletes the unused async path, removes hidden client construction from a model,
and puts Authentication-aware Platform I/O in the module that already owns Science
Platform Server discovery and validation.

### P2 — Split OIDC protocol from interactive CLI presentation

`canfar/auth/oidc.py` is 512 lines and combines four responsibilities:

- discovery, dynamic registration, polling, and refresh HTTP protocol;
- browser launching and QR rendering;
- Rich console output and progress animation;
- mutation of the legacy `OIDC` context model.

The mixed flow is concentrated in `_authflow_impl` at line 344 and `authenticate` at
line 439. `canfar/cli/login_auth.py` is already the natural presentation adapter, but
delegates into a function that prints and opens the browser.

Expose protocol steps and keep presentation in the CLI:

```python
challenge = await start_device_authorization(...)
present_device_challenge(challenge)  # canfar/cli/login_auth.py
tokens = await poll_device_token(challenge, ...)
```

If typed provider payloads are introduced, place the Pydantic domain shapes under
`canfar/models/auth.py`; do not add a parallel DTO layer. Removing QR support is a
product/UX decision, not an automatic code-quality win.

The follow-on
[Authlib feasibility study](../research/2026-07-10-authlib-oidc-replacement.md)
finds that Authlib can replace token request, parsing, expiry, and refresh mechanics,
but not CANFAR's dynamic registration, RFC 8628 coordinator, CLI presentation, or
credential persistence. Adopt it only after a live SKA IAM pilot and only if the
result deletes substantial custom protocol code.

### P2 — Decompose the three branch-density hotspots around existing seams

The largest functions each mix input, policy, I/O, and rendering:

- `canfar/cli/create.py:61` — 159 lines and 11 parameters;
- `canfar/cli/ps.py:32` — 128 lines with a 73-line nested coroutine;
- `canfar/utils/vosi.py:123` — 103 lines with about 17 branch nodes.

Use existing domain objects rather than new request wrappers:

- `create`: parse `KEY=VALUE`, construct `CreateRequest`, run the Session call, and
  render the result in separate functions;
- `ps`: validate raw responses once, filter visible `FetchResponse` models once, then
  choose human or machine rendering;
- VOSI: separate HTTP retrieval from XML parsing and parse the XML exactly once.

This keeps Typer modules as adapters and lets machine output serialize the same
Pydantic models used by library code.

### P2 — Contract the test suite where cases repeat Python or the implementation

`tests/test_helpers_distributed.py` is 1,651 lines for a documented 118-line public
helper module: 65 tests, 182 assertions, 110 `chunk()` calls, 48 `stripe()` calls, and
35 `patch.dict` uses. Most cases manually repeat the same partitions.

A compact table plus invariants preserves more signal:

```python
@pytest.mark.parametrize(
    ("fn", "items", "replica", "total", "expected"),
    [
        (stripe, range(10), 1, 3, [0, 3, 6, 9]),
        (chunk, range(10), 3, 3, [6, 7, 8, 9]),
        (chunk, [1, 2, 3], 4, 5, []),
    ],
)
def test_partition_case(fn, items, replica, total, expected):
    assert list(fn(items, replica=replica, total=total)) == expected
```

Add one invariant that every replica's result is disjoint and the union equals the
input. Resolve `REPLICA_ID` and `REPLICA_COUNT` at call time rather than as default
arguments if environment behavior must be tested without module reloads.

`tests/test_models_types.py` is also 280 lines for static `Literal` aliases. A few
exact `get_args(...)` assertions cover the project contract; annotations,
importability, capitalization, and pairwise-disjointness checks mostly retest Python.

## Ponytail audit — ranked cuts

These lines preserve the requested ponytail-audit format. The maximum estimate
includes optional UX changes; the synthesis following it distinguishes automatic
cuts from product decisions.

shrink: Replace the 1,651-line distributed-helper suite with a parameterized behavior table, one partition-coverage invariant, and focused validation/default tests; about 1,400 lines are removable. [`tests/test_helpers_distributed.py:1`].

delete: Remove the superseded interactive discovery/display path—`display.servers`, `display.capabilities`, `Discover.servers`, module-level `discover.servers`, and `ServerResults`—plus tests that only call that path; keep `server._discover_for_idp` and move the one live style helper into `cli/prompts.py`. About 950 lines are removable. [`canfar/utils/display.py:15`, `canfar/utils/discover.py:137`, `canfar/models/registry.py:85`].

shrink: Collapse the 280-line test suite for static `Literal` aliases to exact tuple assertions and delete the production-unused `Mode` alias; about 240 lines are removable. [`tests/test_models_types.py:1`, `canfar/models/types.py:29`].

yagni: Retire the undocumented legacy `OIDC`/`X509` context mirror and `LegacyContextsMapping` after migrating internal callers to credential models and direct `config.authentication[idp]` updates; about 180 net production lines are removable. [`canfar/models/auth.py:98`, `canfar/models/config_compat.py:1`, `canfar/config/selection.py:135`, `canfar/models/config.py:381`].

delete: Remove test-only or unread state: `Connection`, `TokenAuth`, `ConsoleConfig.file`, and persisted `Server.status`; about 165 lines are removable with their self-tests. [`canfar/models/http.py:304`, `canfar/models/auth.py:262`, `canfar/models/config.py:99`, `canfar/models/http.py:107`].

yagni: Choose one configuration-operation API instead of maintaining service functions and 14 model forwarders as peer surfaces; about 80 lines are removable after call-site migration. [`canfar/models/config.py:270`].

yagni: Inline the one-caller `dict_to_tuples` flattening loop into `create_parameters` and delete its module-only tests; about 50 lines are removable. [`canfar/utils/convert.py:1`, `canfar/utils/build.py:90`].

stdlib: Delete `canfar.cli._run.run` and call `asyncio.run` directly from CLI adapters; the wrapper delegates one standard-library call and has tests of `asyncio.run` semantics. About 45 net lines are removable. [`canfar/cli/_run.py:1`, `tests/test_cli_runner.py:1`].

delete: Remove private `_session`/`_asession` context managers and the no-op `__del__`; public `with client`/`async with client` already provide lifetime behavior. About 40 lines are removable with duplicate tests. [`canfar/client.py:358`, `canfar/client.py:393`, `canfar/client.py:427`].

native: Replace the remaining `questionary` menus with the existing Rich `Prompt` pattern, consolidate the two Science Platform Server selectors, and remove `questionary`; about 35 lines and one dependency are removable. [`canfar/cli/prompts.py:8`, `canfar/cli/auth.py:80`, `pyproject.toml:54`].

delete: Remove or reduce the one-time "mypy is gone" migration-invariant test and remove its runtime `toml` dependency; direct text assertions can retain the invariant without a TOML parser. About 35 lines and one dependency are removable. [`tests/test_pyproject_toolchain.py:1`, `pyproject.toml:57`].

delete: Drop unused `pytest-mock` and `pytest-timeout`; tests use `unittest.mock`, and no timeout marker or pytest timeout setting exists. Two dependencies are removable. [`pyproject.toml:69`].

delete: Drop terminal QR rendering and `segno`; the flow already prints the authorization URL and opens it in the browser. One dependency and a few lines are removable if that UX is intentionally retired. [`canfar/auth/oidc.py:381`, `pyproject.toml:56`].

net: -3,100 lines, -5 deps possible.

### Triage of the ponytail maximum

| Classification | Findings | Decision |
| --- | --- | --- |
| High confidence | duplicated distributed tests; superseded discovery/display; dead types/state; `dict_to_tuples`; private client context helpers; unused pytest plugins | Safe candidates for focused deletion with existing behavior tests. |
| Staged compatibility work | legacy context mirror; dual Configuration/service API | Migrate internals first, deprecate public compatibility, remove only with an explicit compatibility decision. |
| Deliberate small seam | `canfar.cli._run.run` | The cut is real but small. Keeping one event-loop entry point is defensible; do not churn it before higher-value cuts. |
| Product/UX decision | replacing `questionary`; removing QR/`segno` | Do not count as automatic cleanup. Both alter interactive experience. |
| Already planned | all logging and observability work | Execute through issue #100 only. |

The high-confidence, no-UX-change floor is roughly 3,000 lines and three dependencies
(`toml`, `pytest-mock`, and `pytest-timeout`). The two additional dependency cuts in
the maximum estimate require explicit product approval.

## Published improvement program

The review and Authlib research were converted into a native GitHub issue hierarchy
on 2026-07-10. The master roadmap is
[#156 — PRD: Systematic CANFAR client maintainability program](https://github.com/opencadc/canfar/issues/156).
It owns these six PRD sub-issues:

1. [#157 — Contract-focused test and code contraction](https://github.com/opencadc/canfar/issues/157) — 5 implementation sub-issues.
2. [#158 — Configuration and Authentication runtime boundaries](https://github.com/opencadc/canfar/issues/158) — 7 implementation sub-issues.
3. [#159 — Platform and Science Platform Server model purity](https://github.com/opencadc/canfar/issues/159) — 4 implementation sub-issues.
4. [#160 — SRCNet OIDC Authentication with Authlib](https://github.com/opencadc/canfar/issues/160) — 7 implementation sub-issues.
5. [#161 — Session policy and thin CLI adapters](https://github.com/opencadc/canfar/issues/161) — 5 implementation sub-issues.
6. [#100 — Logging Architecture and Observability](https://github.com/opencadc/canfar/issues/100) — clarified in place with 6 implementation sub-issues.

The hierarchy contains 34 tracer-bullet implementation issues and 40 native
blocking links. The two live OIDC gates are deliberately human-owned:
[#177](https://github.com/opencadc/canfar/issues/177) verifies SKA IAM/Authlib
compatibility before token exchange changes, and
[#187](https://github.com/opencadc/canfar/issues/187) verifies login, UserInfo,
refresh, and one read-only Science Platform request after the replacement.

The preferred delivery sequence is:

1. Independent contract tests and mechanical contraction.
2. Atomic Configuration writes and centralized mutation ownership.
3. Deterministic VOSI discovery and OIDC presentation separation.
4. Canonical Authentication Record and HTTP-client resolution.
5. Platform contraction and incremental Authlib adoption.
6. Sync/async Session policy parity.
7. Issue #100 logging on stable HTTP and Authentication seams.
8. Thin `create` and `ps` CLI adapters.
9. Legacy/dead-code contraction and a final whole-program review.

Every implementation issue declares its observable seam, concrete acceptance
criteria, blockers, and the same TDD loop: focused red contract test, smallest green
change, deterministic validation, then a simplification and regression review.

## Review guardrails

- Preserve the public `Session` and `AsyncSession` surfaces and their `list[str]`
  create result contract.
- Do not introduce a separate DTO/request layer; use the domain Pydantic models under
  `canfar/models/`.
- Keep `canfar.helpers.distributed` as documented public API. The audit targets its
  tests, not the helper itself.
- Preserve Authentication and Platform as separate domain seams, and use the glossary
  terms in `CONTEXT.md`.
- Do not combine structural refactors with issue #100's logging behavior migration.
- Run Authentication-dependent integration tests only with a valid CANFAR account and
  X.509 configuration.

## Validation

The audit baseline was verified with:

```text
uv run --no-sync ruff check . --no-cache
All checks passed!

uv run --no-sync ty check canfar
All checks passed!

uv run --no-sync pytest tests -m "not slow" --no-cov -q \
  -o cache_dir=/tmp/canfar-pytest-cache
737 passed in 12.05s

uv run --group docs --no-sync mkdocs build
Documentation built successfully (informational navigation/plugin warnings only).
```

The full auth-dependent test suite was intentionally not run.
