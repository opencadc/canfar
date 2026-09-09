# What's new in the client

## Unreleased: changes since v1.4.1

This guide describes the `feat/interfaces` development branch. The previous
published Python client is [v1.4.1](https://github.com/opencadc/canfar/releases/tag/v1.4.1)
(June 11, 2026). Installing `canfar` from PyPI does not yet provide all the
features below. Follow [Install and set up](get-started.md#install) to choose
a released or development installation, and read the
[upgrade guide](migration.md) before updating scripts.

The branch still reports version `1.4.1` in its package metadata. Check command
help and Python capabilities as well as the version. Platform releases such
as [2026.2](../releases/2026-2.md) have separate numbering and deployment scope.

## Copy and read research data

The new `canfar data` commands let you list, inspect, copy, move, and remove
files using familiar shell operations. Each path names a storage location:
`local` is the computer running the command; configured names such as `arc`
and `vault` identify remote storage. For example, after `canfar login cadc`,
replace `USER` with your username and run:

```bash
canfar data cp local:/data/input.fits arc:/home/USER/input.fits
canfar data cp arc:/home/USER/result.fits local:/data/result.fits
```

You can copy directories with `cp -R`. Recursive removal and moves between
storage locations are unsupported. Use a copy, verify the destination, then
remove only the source files you intend to retire. See
[Data commands](../cli/data.md) and [Data transfers](../platform/storage/transfers.md).

In Python, use `identifiers()` to find configured storage and
`filesystem(identifier)` to read or write it through fsspec, a common Python
filesystem interface. The [data guide](data.md) covers scientific libraries,
short-lived directory-listing caches, explicit whole-file caching, and staging
to `/scratch`. Seeking within an open file does not guarantee a partial
network transfer.

## Log in from Python and choose where to run

`canfar.login()` and `canfar.alogin()` now support OpenID Connect (OIDC) device
login directly from synchronous and asynchronous Python. You open the displayed
verification URL and approve the request with your identity provider (IDP),
the service that manages your account. The CLI can also open a browser and
show a QR code.

Python login saves credentials and discovered servers. You then explicitly
select the identity and a compatible server before creating a Session. Follow
the complete [login and selection example](get-started.md#authenticate).
Storage uses its owning server's IDP: an SRCNet login does not authenticate the
default CADC `arc` or `vault` services.

CADC CLI login can reuse a usable certificate rather than request a new one.
Runtime tokens and certificates passed to an [HTTP client](client.md) take
precedence over saved credentials, including saved-credential refresh and
expiry hooks, for that client only.

## Update scripts and configuration

- Use `-o json` or `-o yaml` on supported commands in place of `--json` and
  `--yaml`. Machine output contains only data on stdout; diagnostics use stderr.
- Use canonical command names such as `auth`, `create`, and `delete`. Several
  alternative spellings were removed; the [migration table](migration.md#update-command-lines)
  lists replacements and the retained deprecated login alias.
- Use `config.editor.get()`, `.set()`, and `.save()` for validated configuration
  edits. The stored schema remains stable; the editing methods moved.
- Use `--log-level` or repeated `-v` before the command. Add `--log-file PATH`
  for a rotating JSON Lines file. Python applications use standard-library
  logging and `canfar.configure_logging()`. See [Logging](../cli/logging.md).
- Set `console.banner` to control the active-server banner in human output.
  Supported machine-output commands omit it automatically.

## Create and inspect Sessions reliably

The synchronous `Session` and asynchronous `AsyncSession` clients continue to
support interactive and headless work, flexible or fixed resources, and
replicas. These capabilities existed in v1.4.1; the current guides clarify
their contracts:

- `create()` returns a list of IDs for successful replicas. Individual HTTP or
  network failures are omitted; total failure returns `[]`. Check the count
  against the number you requested. Validation errors still raise.
- CLI `create --dry-run` previews a request. Machine output reports the creation
  result; it cannot be combined with `--dry-run`. See the [CLI reference](../cli/cli-help.md).
- `fetch()` returns the server's list of dictionaries. The `kind` and `status`
  filters after `destroy_with(prefix)` are keyword-only in both Python clients.
- Verbose logs and events use `canfar.sessions` logging and return `None`.
- [Distributed helpers](helpers.md) remain supported for dividing work among
  replicas, and [Overview](overview.md) remains available for platform availability.

Start with the [Python tutorial](quick-start.md) or
[headless workflow](../platform/sessions/batch.md).

## Where these changes landed

This distinction matters if you have been testing development checkouts:

| Area | Already on main after v1.4.1 | Added or changed on this branch |
| --- | --- | --- |
| Storage | `canfar data`, Python storage access, and caching guidance | Explicit `identifiers()` / `filesystem()` interface replaces dynamic storage imports and public source factories |
| Authentication | Certificate reuse and credential/server workflows | Native Python OIDC login and explicit selection guidance |
| CLI output | Machine output and configurable human banner | `-o/--output`, canonical command names, and consistent request/result models |
| Configuration | Stored authentication and server selections | Bound `config.editor` replaces configuration service methods |
| Logging | Root controls and optional file logging | Smaller implementation using standard-library logging; updated diagnostics and documentation |

For published release history, see the [client changelog](../changelog.md).
