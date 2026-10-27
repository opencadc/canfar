<span id="whats-new-in-canfar"></span>
<span id="recent-updates"></span>

# What's new in the client

## Unreleased changes after v1.5.2

Development builds add installed [CLI extensions](../cli/extensions.md).
Root help and root shell completion list extension names from distribution
metadata. Selecting a command loads its Typer application. The v1.5.2 release
does not include extension discovery.

<span id="unreleased-changes-since-v141"></span>

## Released changes since v1.4.1

The latest published client is [v1.5.2](https://github.com/opencadc/canfar/releases/tag/v1.5.2),
released October 23, 2026. That release includes the data, authentication,
Session, and logging features below. Development builds also add the
extension discovery described above.

Follow [Install and set up](get-started.md#install) to choose an installation,
and read the [upgrade guide](migration.md) before updating scripts written for
v1.4.1. Check command help and Python capabilities as well as the version.
Platform releases such as [2026.3](../releases/2026-3.md) have separate
numbering and deployment scope.

<span id="improved-session-data-validation"></span>

## Copy and read research data

The Data commands and the Python storage tools in `canfar.storage` have been
in beta since v1.5.0. This designation applies to Data. Share your
experience through the [community feedback routes](../platform/community/guidelines.md).

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

Python login saves credentials and discovered servers, prints a status line,
and returns `True` when that Identity Provider has a saved Authentication
Record. An existing record prints `Already authenticated for '<idp>'.` and is
kept unless you pass `force=True`. You then explicitly
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

- `canfar feedback` prints the GitHub feedback URL. It works without login
  or a valid configuration and does not open a browser or collect diagnostics.
- Data group and subcommand help identify the beta. Ordinary commands,
  including file output from `cat`, and Python calls print no beta notice.
- Use `-o json` or `-o yaml` on supported commands in place of `--json` and
  `--yaml`. Machine output contains only data on stdout; diagnostics use stderr.
- Use canonical command names such as `auth`, `create`, and `delete`. Several
  alternative spellings were removed, including the login alias under `auth`;
  the [migration table](migration.md#update-command-lines) lists replacements.
- Use `config.editor.get()`, `.set()`, and `.save()` for validated configuration
  edits. The editing methods moved. A written version 1 file is rewritten as
  version 2 the first time it loads.
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
  `console.file` setting. Loading a version 1 file rewrites it as version 2
  and fills omitted defaults such as `arc` and `vault` on the shipped CADC
  server. See the
  [upgrade guide](migration.md#read-server-limits-from-resources).
- Type a number to choose an Identity Provider or Server when `canfar login`
  or `canfar auth use` asks; the prompts list the choices by number instead of
  using arrow-key menus.
- Request at most 256 replicas per `create` call, down from 512, in both the
  CLI and `CreateRequest`. Split larger runs into several requests.
- Removed `view="all"` and the `View` type from `fetch()` calls. The
  all-Sessions view is no longer supported, and `fetch()` now accepts only
  `kind` and `status`. `stats()`, `logs()`, and `events()` are unchanged.

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

<span id="renew-sessions-and-raise-on-failures"></span>

## Renew Sessions and raise on failures

- `canfar renew SESSION_ID...`, `Session.renew()`, and `AsyncSession.renew()`
  reset the lifetime of interactive Sessions, as the Science Portal does. The
  Python methods return `dict[str, bool]`, like `destroy()`.
- `create`, `info`, `logs`, `events`, `destroy`, `destroy_with`, and `renew`
  accept `errors="ignore"` (the default, unchanged behavior) or
  `errors="raise"`. Raising runs every request first, then reports partial
  results and per-Session errors in `SessionRequestError`. Set the client
  default with `errors=` or `CANFAR_ERRORS`. See
  [Raise on failures](session.md#raise-on-failures).
- `HTTPClient` and the Session clients accept a caller-owned `transport` for
  sharing a connection pool with bearer tokens; closing a client leaves it
  open. See [Share a connection pool](client.md#share-a-connection-pool).

<span id="backend-upgrades"></span>
<span id="previous-versions"></span>
<span id="stay-updated"></span>

## Updated HTTP and storage dependencies

The client requires `httpx2` 2.0.0 or later and Authlib 1.8.0
or later for compatible OpenID Connect clients. If your code handles HTTP
exceptions or supplies test transports, use the corresponding `httpx2` types;
see the [upgrade guide](migration.md#update-http-client-imports).

The storage requirements are `vosfs>=0.12.0` and `fss-cli>=0.11.1`, both
published on PyPI from [opencadc/fsspec-tools](https://github.com/opencadc/fsspec-tools).
`uv.lock` records exact versions and artifact hashes for development installs.
`fss-cli` is the renamed `fsspec-cli` distribution; import it as `fss_cli`.
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

The v1.5.0 release introduced the data commands, native Python OIDC login,
canonical `-o/--output` options, validated `config.editor` edits, Session
renewal, and standard-library logging with `--log-file`. The v1.5.1 release
switched storage dependencies to PyPI. The v1.5.2 release corrected Data help
examples and updated the platform release date. These releases are on main.

For published release history, see the [client changelog](../changelog.md).
