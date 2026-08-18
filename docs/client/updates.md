# What's New in CANFAR

This page highlights the current Python client contracts. For release-by-release
changes, see the [changelog](../changelog.md) and
[GitHub Releases](https://github.com/opencadc/canfar/releases).

## Current Python API

- `Session` and `AsyncSession` are native synchronous and asynchronous clients
  with equivalent public operations.
- `Session.create()` and `AsyncSession.create()` return `list[str]`, omitting
  failed replicas instead of raising for an individual HTTP/network failure.
- `fetch()` returns the server response as `list[dict[str, str]]`.
- `destroy_with(prefix, *, kind=..., status=...)` keeps its keyword-only filter
  contract in both clients.
- `canfar.login()` and `canfar.alogin()` provide synchronous and asynchronous
  Python Authentication flows. OIDC device login prints a verification URL and
  user-facing code to the terminal; browser, QR, and progress presentation stay
  in the CLI.
- `config.editor.get()`, `set()`, and `save()` are the supported Configuration
  editing operations. The persisted Configuration shape remains stable.
- `canfar.storage.identifiers()` and `canfar.storage.filesystem(identifier)` are
  the explicit VOSpace Python surface. Storage Identifiers are not dynamic
  module members or fsspec schemes.
- `Overview` and `canfar.helpers.distributed` remain supported public APIs.

Start with the [Python quickstart](quick-start.md), then see the [Session API](session.md),
[Data Access](data.md), and [Migration Guide](migration.md).
