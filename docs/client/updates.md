<span id="whats-new-in-canfar"></span>
<span id="recent-updates"></span>

# What's new in the client

## Unreleased: changes since v1.4.1

This guide describes the development client after v1.4.1. The previous
published Python client is [v1.4.1](https://github.com/opencadc/canfar/releases/tag/v1.4.1)
(June 11, 2026). Installing `canfar` from PyPI does not yet provide all the
features below. Follow [Install and set up](get-started.md#install) to choose
a released or development installation, and read the
[upgrade guide](migration.md) before updating scripts.

The development checkout still reports version `1.4.1` in its package metadata.
Check command help and Python capabilities as well as the version. Platform releases such
as [2026.2](../releases/2026-2.md) have separate numbering and deployment scope.

<span id="improved-session-data-validation"></span>

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

<span id="enhanced-authentication-system"></span>

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
If it has expired, `canfar login cadc` asks for your credentials again without
requiring `--force`. `canfar login srcnet` starts a fresh device login even
when a saved record exists. SRCNet access-token refresh now checks the
separate client-secret expiry when the IDP supplies it. Missing, expired, or
rejected refresh credentials produce an IDP-specific login instruction;
temporary IDP failures preserve the saved record for a retry. See
[Authentication and Servers](../cli/authentication-contexts.md#login).

Runtime tokens and certificates passed to an [HTTP client](client.md) take
precedence over saved credentials, including saved-credential refresh and
expiry hooks, for that client only.

<span id="logs-to-stdout"></span>

## Update scripts and configuration

- Use `-o json` or `-o yaml` on supported commands in place of `--json` and
  `--yaml`. Machine output contains only data on stdout; diagnostics use stderr.
- Use canonical command names such as `auth`, `create`, and `delete`. Several
  alternative spellings were removed, including the login alias under `auth`;
  the [migration table](migration.md#update-command-lines) lists replacements.
- Use `config.editor.get()`, `.set()`, and `.save()` for validated configuration
  edits. The stored schema remains stable; the editing methods moved.
- Use `--log-level`, `-v` (`info`: one line per Science Platform HTTP
  response), or `-vv` (`debug`) before the command; `-v` previously selected
  `error`, and `info` needed `-vvv`. Add `--log-file PATH` for a rotating JSON
  Lines file. Python applications use standard-library logging and
  `canfar.configure_logging()`. See [Logging](../cli/logging.md).
- Name local files `local:/PATH` in `canfar data`. Each data command's
  `--help` now explains the `IDENTIFIER:/PATH` syntax and lists the configured
  identifiers, and a rejected bare local path prints a hint.
- Set `console.banner` to control the active-server banner in human output.
  Supported machine-output commands omit it automatically.
- Read Server limits from `resources`. The flat `cores`, `ram`, and `gpus`
  Server fields are gone, as are the unused Server `status` field and
  `console.file` setting; saved configurations still load. See the
  [upgrade guide](migration.md#read-server-limits-from-resources).
- Type a number to choose an Identity Provider or Server when `canfar login`
  or `canfar auth use` asks; the prompts list the choices by number instead of
  using arrow-key menus.
- Request at most 256 replicas per `create` call, down from 512, in both the
  CLI and `CreateRequest`. Split larger runs into several requests.

<span id="server-resources"></span>

## See which Servers connect and what they offer

While it discovers Servers, `canfar login` shows a live grid: one square per
Server, filling in as each Server answers, and a legend that counts the ones
discovered, timed out, unreachable, or failed. Each Server is checked and
inspected on its own, so slow Servers no longer hold back the rest. A summary
line gives the number of Servers checked and the request timeout, and suggests
a longer `--timeout` when Servers time out. `--log-level info` labels the
squares with Server Names, and output without color uses a distinct glyph per
outcome. Newly discovered Servers are saved; a Server saved by an earlier login
stays selectable even if it does not answer this time. When none is
discovered, the grid still shows why before the error. The registry timing
line ("Fetched ... in Ns") is now an INFO log record instead of console
output.

Each discovered Server also reports the Session limits it advertises: what a
flexible Session is guaranteed and can burst to, the smallest and largest
fixed CPU and memory values, GPUs, and the number of interactive Sessions per
user. `canfar server ls` shows them, `canfar server ls -o json` returns them
under `resources`, and `canfar create` rejects a `--cpu`, `--memory`, or
`--gpu` value outside the active Server's limits before sending the request.
A limit the Server does not advertise stays unknown rather than defaulted. See
[What your Server offers](../platform/sessions/limits.md#what-your-server-offers).

<span id="asynchronous-sessions"></span>
<span id="destroy-sessions"></span>

<span id="firefly-support"></span>
<span id="private-images"></span>

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

<span id="backend-upgrades"></span>
<span id="previous-versions"></span>
<span id="stay-updated"></span>

## Updated HTTP and storage dependencies

The development client uses `httpx2` 2.13.1 or later and requires Authlib 1.8.0
or later for compatible OpenID Connect clients. If your code handles HTTP
exceptions or supplies test transports, use the corresponding `httpx2` types;
see the [upgrade guide](migration.md#update-http-client-imports).

The storage dependencies are pinned to `vosfs` 0.11.0 and `fsspec-cli` 0.10.0.
Recursive copies can be rerun into an existing destination directory and skip
files only after verifying their contents. See [Data commands](../cli/data.md).
These releases reduce requests during tree and bulk operations and report
per-file transfers when you use `canfar -v data cp`; see
[Logging](../cli/logging.md).
The runtime, development, and documentation dependency requirements and
lockfile have also been refreshed. Python 3.10 remains supported.

The client no longer depends on `cadcutils`, `questionary`, or `click`.
`canfar login cadc` requests the proxy certificate from the CADC credential
service directly, interactive choices are numbered prompts, and command
choices come from Typer. If you use `cadc-get-cert` or import `cadcutils`,
install it yourself; see the
[upgrade guide](migration.md#install-cadcutils-for-cadc-tools).

## Where these changes landed

The interfaces described above have landed on main since v1.4.1. This
dependency update builds on them:

| Area | Main after v1.4.1 | This dependency update |
| --- | --- | --- |
| Storage | `canfar data`, explicit `identifiers()` / `filesystem()`, and caching guidance | `vosfs` 0.11.0 and `fsspec-cli` 0.10.0, including verified recursive-copy resumption and transfer logging |
| Authentication | Native Python OIDC login, certificate reuse, and explicit credential/server selection | Authlib 1.8.0 or later for `httpx2` compatibility |
| HTTP transport | Native synchronous and asynchronous HTTP clients | `httpx2` clients, exceptions, and test transports |

Canonical `-o/--output` commands, validated `config.editor` edits, and
standard-library logging with `--log-file` are also on main after v1.4.1;
follow the [upgrade guide](migration.md) when moving from the published client.

For published release history, see the [client changelog](../changelog.md).
