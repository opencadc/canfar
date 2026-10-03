<span id="python-equivalents"></span>

# Authentication and Servers

CANFAR keeps identity and routing separate:

- **Authentication** owns the user's identity and credentials.
- An **Identity Provider (IDP)** issues that identity. The built-in keys are
  `cadc` (X.509) and `srcnet` (OIDC Device Authorization).
- A **Science Platform Server** runs Sessions.
- **Server Selection** chooses the Science Platform Server for new requests.

The active Authentication Record and Server Selection are saved together in
the local Configuration. Existing Sessions remain on the Science Platform
Server where they were launched.

<span id="log-in"></span>

## Login

```bash
canfar login [IDP]
```

When `IDP` is omitted, the CLI prompts for one. Use these options when needed:

| Option | Effect |
| --- | --- |
| `--force`, `-f` | Obtain a new CADC certificate even when the current one is valid. |
| `--dev` | Include development registries and endpoints during Server Discovery. |
| `--timeout`, `-t` | HTTP timeout in seconds for login requests; default `10`. |

Login authenticates the selected IDP, discovers compatible Science Platform
Servers, and saves the Authentication Record and Server Selection. When several
compatible Servers are discovered, the CLI lists them by number and asks you to
type the number of the one to use; the IDP prompt works the same way. You can log in again when an Authentication Record already
exists; `--force` is not required to recover expired credentials.

<span id="discovery-outcomes"></span>

### Discovery outcomes

While it discovers Servers, login shows a live grid on stderr: one square per
Server, in Server Name order, redrawn every second. A hollow square is still
being checked; it fills in with its outcome as soon as that Server answers or
fails, so slow Servers do not hold back the others. A legend counts each
outcome:

```text
■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
■ 14 discovered   ■ 5 timeout   ■ 4 unreachable   ■ 2 failed
Checked 25 servers in 13.2s with a 10s request timeout.
5 timed out. To wait longer, run canfar login srcnet --timeout 20
```

| Outcome | Without color | Meaning |
| --- | --- | --- |
| discovered | `+` | The Server answered and published usable session capabilities. |
| timeout | `~` | The Server did not answer within `--timeout` seconds. |
| unreachable | `x` | The connection failed, for example on DNS or TLS. |
| failed | `!` | The Server answered, but with an error status or unusable capabilities. |
| pending | `.` | The Server is still being checked. |

When stderr has no color, for example in a CI log or with `NO_COLOR` set, each
outcome uses the glyph in the second column instead of a colored square. When
the registries list only one Server, as for `canfar login cadc`, login skips
the squares and legend and prints only the summary lines.

The last lines report how many Servers were checked, how long that took, and
the request timeout. When a Server times out, login prints the same login
command with a doubled `--timeout`, up to the 300-second limit. If discovery
is interrupted, for example with Ctrl-C, the last line instead says how many
Servers were not checked. If no registry can be read, login shows no grid; it
prints the error and suggests checking the network or a longer `--timeout`.

Newly discovered Servers are saved, and when none is discovered the grid still
appears before the error. A Server saved by an earlier login stays available
for selection with its saved details even if it times out or fails this time.
Each discovered Server also reports its Session limits; see
[Server Selection](#manage-servers). Add `-v` (or `--log-level info`) before
`login` to label each square with its Server Name and to log how long each
registry took, and `--log-level debug` for the reason behind each outcome:

```bash
canfar --log-level info login srcnet
```

### CADC X.509

```bash
canfar login cadc
```

The CLI reuses a usable X.509 certificate when possible. If the certificate
is missing or expired, login asks for your CADC credentials to obtain a new
one. Use `--force` to replace a certificate that is still valid. Ordinary
commands cannot renew an expired certificate; run `canfar login cadc` yourself.

The certificate is saved as `~/.ssl/cadcproxy.pem` and is valid for 30 days.
The [legacy CADC tools](../platform/storage/vospace.md#legacy-vostools) read
the same file, so one login serves both. Inside a Session on the CADC
deployment, the Server places a delegated certificate at that path when the
Session starts, and `~/.canfar` lives in your persistent home directory, so a
login made in one Session is there in the next. For unattended work, log in
from the environment that will run the job and check that the certificate
outlasts it.

### SRCNet OIDC Device Authorization

```bash
canfar login srcnet
```

Each explicit `canfar login srcnet` performs OIDC discovery and fresh dynamic
client registration, then presents the Device Authorization challenge in the
terminal, even when you have a saved Authentication Record:

1. It prints a verification URL, user code, and a terminal QR code.
2. It opens the verification URL in the default browser when possible.
3. You sign in and approve the request in the browser.
4. The CLI polls for approval and shows progress until the IDP returns tokens.

If the browser cannot be opened, visit the printed URL manually. The device
challenge has an IDP-provided expiry; `--timeout` controls HTTP requests and
does not extend that challenge. Denial, expiry, malformed responses, and
network failures stop login with an error; run the command again after fixing
the cause.

Ordinary commands use a valid access token or refresh it without opening a
browser. The access token, refresh token, and registered client secret have
separate lifetimes. CANFAR saves the client-secret expiry reported by the IDP;
it does not assume a fixed lifetime. An expired client secret prevents refresh
but does not prevent use of an access token that is still valid. Older records
without that expiry can still attempt refresh.

When refresh credentials are missing, known to be expired, or rejected by the
IDP, run `canfar login srcnet` and approve the new device challenge. A timeout
or temporary IDP failure leaves your saved credentials intact so you can retry
the command.

For troubleshooting, put root logging options before `login`:

```bash
canfar --log-level debug login srcnet
canfar --log-level debug login cadc --force
```

See [Logging](logging.md) for precedence and stream routing.

<span id="machine-output-rules"></span>

## Inspect Authentication

```bash
canfar auth
canfar auth show
canfar auth ls
```

Bare `canfar auth` defaults to `auth show`. Human output includes the active
Server Selection when one is available. For scripts, use machine output on the
data-producing form:

```bash
canfar auth show -o json
canfar auth ls --output yaml
```

The machine payload is an Authentication object or list of Authentication
objects. It contains the canonical IDP key, display name, Authentication Mode,
expiry, active state, and associated Server Name; it does not contain raw
credential material.

<span id="remove-saved-auth-state"></span>

<span id="switch-idp"></span>

## Change or remove state

Switch to a saved Authentication Record by canonical IDP key:

```bash
canfar auth use srcnet
canfar auth use cadc
```

When switching, CANFAR reuses a compatible remembered Server Selection when
one exists. If several compatible Servers need a choice, the CLI lists them by
number and prompts for one.

Remove one Authentication Record and its associated Servers with:

```bash
canfar auth rm srcnet
canfar auth rm srcnet --force
```

Removing the active Authentication asks for confirmation unless `--force` is
used. To reset all Authentication and Server state, use the required force
flag:

```bash
canfar auth purge --force
```

The purge restores built-in defaults and preserves unrelated registry and
console settings. These are the commands for leaving an identity; there is no
separate logout command.

<span id="manage-servers"></span>

## Server Selection

```bash
canfar server ls
canfar server ls -o json
canfar server use SELECTOR
```

`server ls` lists the saved Servers for the active IDP. If none are saved, it
runs discovery and persists the result. Its machine payload is a list of
Server records and is data-only on stdout.

Alongside each Server's URI and URL, the table shows the Session limits the
Server advertises, and a caption under the table summarizes the columns:

| Column | Meaning |
| --- | --- |
| Flexible | Cores and memory a Session without `--cpu` or `--memory` is guaranteed, and what it can burst to. |
| Fixed | The smallest and largest `--cpu` and `--memory` values the Server accepts. |
| GPUs | The `--gpu` values the Server accepts, or `none`. |
| Sessions | How many interactive Sessions you can run at once; `headless` Sessions do not count. |

`unknown` marks a limit the Server does not advertise, as older platform
versions may not. The machine payload carries the same values in each
Server's `resources`, with `null` for unknown. Discovery reads the limits, and
`server use` reads them again for the selected Server. `canfar create` rejects
values outside the active Server's known limits; see
[Session limits](../platform/sessions/limits.md#what-your-server-offers).

`server use` accepts either a Server Name or an IVOA URI:

```bash
canfar server use canfar
canfar server use ivo://cadc.nrc.ca/skaha
```

The persisted `active.server` value is the Server Name. The IVOA URI is
discovery metadata and can still be used as a selector.

<span id="configuration"></span>

## Configuration shape

The persisted shape separates Authentication Records and Science Platform
Servers. `active.server` refers to a Server Name, not an IVOA URI:

```yaml
version: 1
active:
  authentication: cadc
  server: canfar
authentication:
  cadc:
    mode: x509
servers:
  canfar:
    idp: cadc
    uri: ivo://cadc.nrc.ca/skaha
    url: https://ws-uv.canfar.net/skaha
    resources:
      flexible:
        cores: {min: 1, max: 16}
        ram: {min: 4, max: 32}
      fixed:
        cores: {min: 1, max: 16}
        ram: {min: 1, max: 192}
      sessions: 5
```

`resources` is written by discovery and `server use`; it is absent until a
Server has reported its limits.

Use `canfar config get` and `canfar config set` for dotted configuration
paths. Values passed to `config set` are parsed as YAML:

```bash
canfar config get active.server
canfar config get servers.canfar.url
canfar config set console.banner false
```

Environment overrides use the same nested names, for example:

```bash
CANFAR_CONSOLE__BANNER=false canfar auth show
```

The complete command and machine-output contract is in the [CLI reference](cli-help.md).
