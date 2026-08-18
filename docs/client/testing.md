# Testing

CANFAR uses [pytest](https://pytest.org/). Tests mirror the `canfar/` module
layout and include deterministic unit/contract tests plus
Authentication-dependent integration tests.

## Prerequisites

Install the project environment with `uv`. Full integration coverage requires a
valid CANFAR Authentication Record and X.509 certificate/configuration. Do not
run that suite against a real account unless the test workflow is explicitly
intended to create or clean up platform resources.

## Local validation

The default local test gate excludes slow tests and avoids external
Authentication:

```bash
uv run --no-sync pytest tests -m "not slow" --no-cov -q \
  -o cache_dir=/tmp/canfar-pytest-cache
```

Useful focused checks include:

```bash
uv run --no-sync pytest tests/test_sessions_fetch.py tests/test_sessions_lifecycle.py \
  tests/test_storage.py tests/test_config_editor.py -q
uv run --no-sync ruff check . --no-cache
uv run ty check canfar
uv run --group docs mkdocs build
```

The documentation build is the check for broken navigation, Markdown, and
generated Python API pages.

## Test markers

Use markers to select known test categories:

```bash
uv run --no-sync pytest -m unit
uv run --no-sync pytest -m integration
uv run --no-sync pytest -m slow
```

Integration and slow tests may contact CANFAR services and require valid
credentials. `-m "not slow"` is the deterministic default; it is not a claim
that every test marked `integration` is safe without Authentication.

## Full suite

Run the full suite only in an environment prepared for the credentialed gate:

```bash
uv run --no-sync pytest
```

The full run includes Authentication-dependent tests, Session lifecycle work,
and network operations. A local failure can therefore indicate missing
credentials or unavailable Science Platform infrastructure rather than a
library regression.

## Adding tests

- Mirror the source module path under `tests/`.
- Mark network or long-running tests with `integration` and/or `slow`.
- Prefer observable public seams such as `httpx.MockTransport`, `CliRunner`,
  and the public Configuration editor.
- Keep sync tests synchronous and async tests on the native async path.
