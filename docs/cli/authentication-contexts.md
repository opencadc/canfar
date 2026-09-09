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

## Login

```bash
canfar login [IDP]
```

When `IDP` is omitted, the CLI prompts for one. Use these options when needed:

| Option | Effect |
| --- | --- |
| `--force`, `-f` | Obtain new credentials and rediscover instead of refusing an existing record. |
| `--dev` | Include development registries and endpoints during Server Discovery. |
| `--timeout`, `-t` | HTTP timeout in seconds for login requests; default `10`. |

Login authenticates the selected IDP, discovers compatible Science Platform
Servers, selects one when necessary, and saves the Authentication Record and
Server Selection. A saved record causes a repeat login to fail unless
`--force` is supplied.

### CADC X.509

```bash
canfar login cadc
```

The CLI reuses a usable X.509 certificate when possible. Use `--force` to
obtain a replacement. If the certificate is expired, login reports that and
continues with certificate acquisition.

### SRCNet OIDC Device Authorization

```bash
canfar login srcnet
```

The CLI performs OIDC discovery and dynamic client registration, then presents
the Device Authorization challenge in the terminal:

1. It prints a verification URL, user code, and a terminal QR code.
2. It opens the verification URL in the default browser when possible.
3. You sign in and approve the request in the browser.
4. The CLI polls for approval and shows progress until the IDP returns tokens.

If the browser cannot be opened, visit the printed URL manually. The device
challenge has an IDP-provided expiry; `--timeout` controls HTTP requests and
does not extend that challenge. Denial, expiry, malformed responses, and
network failures stop login with an error; run the command again after fixing
the cause.

For troubleshooting, put root logging options before `login`:

```bash
canfar --log-level debug login srcnet
canfar --log-level debug login cadc --force
```

See [Logging](logging.md) for precedence and stream routing.

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

## Change or remove state

Switch to a saved Authentication Record by canonical IDP key:

```bash
canfar auth use srcnet
canfar auth use cadc
```

When switching, CANFAR reuses a compatible remembered Server Selection when
one exists. If several compatible Servers need a choice, the CLI prompts for a
Server URI or list number.

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
console settings.

## Server Selection

```bash
canfar server ls
canfar server ls -o json
canfar server use SELECTOR
```

`server ls` lists the saved Servers for the active IDP. If none are saved, it
runs discovery and persists the result. Its machine payload is a list of
Server records and is data-only on stdout.

`server use` accepts either a Server Name or an IVOA URI:

```bash
canfar server use canfar
canfar server use ivo://cadc.nrc.ca/skaha
```

The persisted `active.server` value is the Server Name. The IVOA URI is
discovery metadata and can still be used as a selector.

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
```

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
