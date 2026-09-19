# CLI reference

The `canfar` command manages Authentication, Science Platform Server
selection, Sessions, Container Images, data sources, and client configuration.
Run `canfar --help` or append `--help` to any command for the installed
options.

## Canonical command surface

The root keeps Session and information operations as leaves. Authentication,
Server, data, image, and configuration operations remain grouped:

| Area | Commands |
| --- | --- |
| Authentication and Server Selection | `login`, `auth`, `server` |
| Sessions | `create`, `ps`, `events`, `info`, `open`, `logs`, `delete`, `prune` |
| Platform information | `stats`, `image ls` |
| Client configuration | `config show`, `config get`, `config set`, `config path`, `version` |
| Data | `data` and its embedded file commands |

There are no extra command names between the root and these leaves. In
particular, Session creation is `canfar create`, and login is `canfar login`.

<span id="root-logging-controls"></span>

## Root logging options

Root logging options must come before the command:

```bash
canfar --log-level debug ps
canfar -vvv ps
canfar --log-file ./logs/canfar.jsonl ps
```

| Option | Effect |
| --- | --- |
| `--log-level LEVEL` | `critical`, `error`, `warning`, `info`, or `debug`. |
| `-v` | Increase verbosity; four or more repetitions select `debug`. |
| `--log-file PATH` | Add the rotating JSON Lines file sink. |

See [Logging](logging.md) for precedence, stream routing, file records, and
setup errors.

<span id="canfar-auth"></span>

## Authentication and Servers

<span id="canfar-login"></span>

### Login

```text title="Command syntax"
canfar login [IDP] [OPTIONS]
```

`IDP` is an optional canonical Identity Provider key. Without it, the CLI
prompts for one. The options are:

| Option | Effect |
| --- | --- |
| `--force`, `-f` | Re-authenticate an existing Authentication Record. |
| `--dev` | Include development registries and endpoints during discovery. |
| `--timeout`, `-t` | HTTP timeout in seconds; default `10`. |

```bash
canfar login cadc
canfar login srcnet --force
```

The interactive credential flow and Server Selection are described in
[Authentication and Servers](authentication-contexts.md).

### Authentication

```text title="Command syntax"
canfar auth
canfar auth show
canfar auth ls
canfar auth use IDP
canfar auth rm IDP [--force]
canfar auth purge --force
```

`canfar auth` is the same active-Authentication view as `canfar auth show`.
`auth use` selects a saved Authentication Record; `auth rm` also removes the
associated Servers; `auth purge --force` resets Authentication and Server state.

<span id="canfar-server"></span>

### Server Selection

```bash
canfar server ls
canfar server use SELECTOR
```

`SELECTOR` may be a Server Name or an IVOA URI. `server ls` lists Servers for
the active IDP and discovers them when no saved Servers are available.

## Sessions

<span id="canfar-create"></span>

### Create

```text title="Command syntax"
canfar create [OPTIONS] KIND IMAGE [-- CMD [ARGS]...]
```

`KIND` is one of `desktop`, `notebook`, `carta`, `headless`, `firefly`, or
`contributed`. `IMAGE` is a CANFAR Container Image such as
`skaha/astroml:latest`; the client adds the CANFAR registry and `:latest` when
they are omitted. That shorthand always expands to `images.canfar.net`, so on a
Server that trusts another registry, write the full `REGISTRY/PROJECT/IMAGE:TAG`
name from `canfar image ls`. Accepted ranges for every option are in
[Session limits](../platform/sessions/limits.md).

| Option | Effect |
| --- | --- |
| `--name`, `-n` | Session name; a generated name is used by default. |
| `--cpu`, `-c` | Requested CPU cores. |
| `--memory`, `-m` | Requested RAM in GB. |
| `--gpu`, `-g` | Requested GPU count. |
| `--env`, `-e KEY=VALUE` | Set an environment variable; repeat as needed. |
| `--replicas`, `-r` | Number of Sessions, 1 to 512; default `1`. |
| `--debug` | Print the parsed Session request. |
| `--dry-run` | Validate and print the request without creating a Session. |
| `--output`, `-o` | Emit created Session IDs as `json` or `yaml`. |

Everything after `--` belongs to the container command. The first token is
the command and the remaining tokens are its arguments, even when they look
like CANFAR options:

```bash
canfar create headless skaha/terminal:1.1.2 -- python /arc/projects/demo/run.py
canfar create headless skaha/terminal:1.1.2 -- worker --output json -o yaml
```

The `--output` option must appear before `--`. `--dry-run` cannot be combined
with machine output.

<span id="canfar-ps"></span>

### List Sessions

```text title="Command syntax"
canfar ps [OPTIONS]
```

| Option | Effect |
| --- | --- |
| `--all`, `-a` | Include all statuses; otherwise show `Pending` and `Running`. |
| `--quiet`, `-q` | Print matching Session IDs in human mode. |
| `--kind`, `-k` | Filter by Session Kind. |
| `--status`, `-s` | Pass a status filter to the Science Platform. |
| `--debug` | Print Session response warnings. |
| `--output`, `-o` | Emit the filtered Session response array as `json` or `yaml`. |

`ps` stays a thin operation over `Session.fetch()`: `--kind` and `--status`
are sent to the fetch call, then the CLI applies the running/default or
`--all` view to the returned responses. `--quiet` follows that same filter,
including when combined with `--all`, and is not available with `--output`.

```bash
canfar ps
canfar ps --all --kind headless
canfar ps -o json
```

<span id="inspect-and-clean-up"></span>

### Inspect, open, and remove

These leaves accept one or more Session IDs and produce human-readable output:

| Command | Purpose |
| --- | --- |
| `canfar events SESSION_ID...` | List Science Platform events. |
| `canfar info SESSION_ID...` | Show Session details; `--debug` adds response warnings. |
| `canfar logs SESSION_ID...` | Show Session logs. |
| `canfar open SESSION_ID...` | Open ready Sessions in new browser tabs. |
| `canfar delete SESSION_ID... [--force]` | Delete Sessions, confirming unless `--force` is used. |
| `canfar prune PREFIX [KIND] [STATUS]` | Delete matching names; defaults to `headless` and `Succeeded`. |

`prune` treats a plain `PREFIX` as a literal prefix. A value containing regex
metacharacters is treated as a regular expression. Quote such values so the
shell does not expand them:

```bash
canfar prune 'notebook.*' notebook Completed
```

<span id="images-and-platform-state"></span>

### Platform information

```bash
canfar stats
canfar image ls
canfar image ls --kind notebook
canfar version
canfar version --debug
```

`stats` prints platform usage tables. `image ls` lists Container Images and
accepts the image-kind filter shown above. `version --debug` prints client,
Python, operating-system, and dependency details for a bug report; it is not a
logging control.

<span id="data"></span>
<span id="client-configuration"></span>

## Data and configuration

```bash
canfar data --help
canfar config show
canfar config get console.width
canfar config set console.width 132
canfar config path
```

Data operands use an explicit `Storage Identifier`, for example
`arc:/home/user/file.fits` or `local:/tmp/file.fits`. See [Data commands](data.md)
for the embedded command surface. Configuration keys use dotted paths; values
passed to `config set` are parsed as YAML. See [Authentication and Servers](authentication-contexts.md)
for the persisted Authentication, Server, and active-selection shape.

<span id="machine-output-contract"></span>

## Machine output

The leaf option `-o/--output` accepts only `json` or `yaml`. It is available on
the data-producing forms `auth` (the default active view), `auth show`,
`auth ls`, `server ls`, `create`, `ps`, `config show`, and `config get`:

```bash
canfar auth show -o json
canfar server ls --output yaml
canfar create headless skaha/terminal:1.1.2 -o json
canfar config get active.server -o json
```

The payload is the same Python result used by that command after its normal
filtering. For example, `create -o json` is a raw list of Session IDs and
`ps -o json` is a filtered array of Session response objects; neither is
wrapped in a command-specific envelope. Human active-Server banners and logs
never precede the machine payload on stdout. Diagnostics and errors use stderr.

### Failures and exit status

A command that fails exits with a nonzero status. In human mode the message
and a hint go to stderr. In machine mode stderr carries one structured object
with a stable `code`, a `message`, and a `hint`, and stdout stays empty:

```json
{"code": "authentication.required", "message": "Not authenticated with 'cadc'.\nReason: X.509 certificate has not been issued.", "hint": "Run `canfar login` and retry."}
```

| Code | Meaning | Next step |
| --- | --- | --- |
| `authentication.required` | No credential is saved for the active Identity Provider. | Run `canfar login`. |
| `authentication.expired` | The saved credential has expired. | Run `canfar login` again. |
| `authentication.credential_invalid` | A credential is saved but cannot be used, such as an unreadable certificate. | Check `canfar auth show`, then log in again. |
| `transport.failure` | The request did not reach, or was refused by, the Science Platform Server. | Check connectivity and `canfar stats`, then retry. |

Codes are stable; message and hint wording can change. Every command that
contacts a Server reports a missing login this way, including the human-text
commands `info`, `events`, `logs`, `open`, `stats`, and `image ls`.

Put `-o/--output` after the command that owns it. Root `-o`, `--json`, and
`--yaml` are not options, and commands without machine output reject `-o`.
For `create`, `-o` is parsed only before `--`; after the delimiter it is a
container-command token.
