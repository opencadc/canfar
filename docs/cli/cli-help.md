# CLI Reference

Use `canfar` for Authentication, Science Platform Server selection, Session
management, Container Images, and client configuration.

```bash
canfar --help
```

## Root logging controls

Put logging options before the command:

```bash
canfar --log-level debug ps
canfar -vvv ps
canfar --log-file ./logs/canfar.jsonl ps
```

| Option | Use |
| --- | --- |
| `--log-level LEVEL` | Select `critical`, `error`, `warning`, `info`, or `debug`. |
| `-v` | Increase verbosity; repeat through `-vvvv` for `debug`. |
| `--log-file PATH` | Add the rotating JSON Lines file sink. |

See [Logging](logging.md) for the exact mapping, precedence, streams, file
schema, and stable error codes.

## Authentication and Servers

### `canfar login`

```bash
canfar login [IDP] [OPTIONS]
```

| Option | Use |
| --- | --- |
| `--force`, `-f` | Force re-authentication. |
| `--dev` | Include development Servers during discovery. |
| `--timeout`, `-t` | HTTP timeout in seconds during login. Default: `10`. |

Examples:

```bash
canfar login
canfar login cadc
canfar login srcnet --force
```

`canfar auth login` is a deprecated compatibility alias.

### `canfar auth`

```bash
canfar auth
canfar auth show
canfar auth ls
canfar auth use IDP
canfar auth rm IDP [--force]
canfar auth purge --force
```

| Command | Use |
| --- | --- |
| `auth` / `auth show` | Show active Authentication state. |
| `auth ls` | List saved Authentication records. |
| `auth use IDP` | Switch active Authentication by canonical IDP key. |
| `auth rm IDP` | Remove one Authentication record and its Servers. |
| `auth purge --force` | Reset Authentication and Server state. |

Machine output is supported for `auth` / `auth show` and `auth ls`:

```bash
canfar auth show --json
canfar auth ls --yaml
```

### `canfar server`

```bash
canfar server ls
canfar server use SELECTOR
```

| Command | Use |
| --- | --- |
| `server ls` | List Servers for the active IDP, discovering them when needed. |
| `server use SELECTOR` | Select a Server by name or URI. |

Use URIs in scripts because names can be ambiguous:

```bash
canfar server use ivo://cadc.nrc.ca/skaha
```

## Sessions

### `canfar create`

```bash
canfar create [OPTIONS] KIND IMAGE [-- CMD [ARGS]...]
```

| Option | Short | Use |
| --- | --- | --- |
| `--name` | `-n` | Session name. Defaults to a generated name. |
| `--cpu` | `-c` | Fixed CPU cores. Omit for flexible allocation. |
| `--memory` | `-m` | Fixed RAM in GB. Omit for flexible allocation. |
| `--gpu` | `-g` | GPU count. |
| `--env` | `-e` | Environment variable as `KEY=VALUE`. |
| `--replicas` | `-r` | Number of replicas. Default: `1`. |
| `--debug` | | Print parsed Session request details. |
| `--dry-run` | | Parse parameters and exit. |
| `--json` | | Emit created Session IDs as a JSON list. |
| `--yaml` | | Emit created Session IDs as a YAML list. |

`--json` and `--yaml` are mutually exclusive. `--dry-run` is human-output only.

Examples:

```bash
canfar create notebook skaha/astroml:latest
canfar create --cpu 4 --memory 16 notebook skaha/astroml:latest
canfar create headless skaha/terminal:1.1.2 -- python /arc/projects/demo/run.py
```

### `canfar ps`

```bash
canfar ps [OPTIONS]
```

| Option | Short | Use |
| --- | --- | --- |
| `--all` | `-a` | Show all Sessions. Default shows running Sessions. |
| `--quiet` | `-q` | Print only Session IDs. |
| `--kind` | `-k` | Filter by Session Kind. |
| `--status` | `-s` | Filter by status. |
| `--debug` | | Show Session response warnings. |

Machine output:

```bash
canfar ps --json
canfar ps --yaml
```

`--quiet` is a human-output shortcut and is incompatible with machine output.

### Inspect and clean up

```bash
canfar events SESSION_ID...
canfar info SESSION_ID...
canfar logs SESSION_ID...
canfar open SESSION_ID...
canfar delete SESSION_ID... [--force]
canfar prune PREFIX [KIND] [STATUS]
```

Quote `PREFIX` when it contains shell metacharacters
(for example `canfar prune 'rabi.*' headless Completed`).

`canfar info SESSION_ID --debug` shows Session response warnings. This is
a command diagnostic, not a logging-level control.

Common flow:

```bash
canfar ps
canfar info $(canfar ps -q)
canfar open $(canfar ps -q)
canfar delete $(canfar ps -q)
```

## Images and platform state

```bash
canfar image ls
canfar stats
```

Use `canfar image --help` and `canfar stats --help` for command-specific
options.

## Data

```bash
canfar data ls -lh canfar:/
canfar data cp local:/absolute/path/file.fits canfar:/folder/file.fits
```

Data operands use explicit `Storage-Name:/absolute/path` or
`local:/absolute/path` syntax. See [Data commands](data.md) for recursive copy,
cross-source copy and verification, recursive-removal policy, and the exact
supported boundary.

## Client configuration

```bash
canfar config show
canfar config path
canfar config get console.width
canfar config get servers.canfar.url
canfar config set console.width 132
canfar config set console.banner false
canfar version
canfar version --debug
```

`config set` parses values as YAML.
`console.banner` defaults to `true`. Set it to `false` to hide the
`@<server-name>` prefix from human-readable CLI output. The banner is always
disabled for `--json` and `--yaml` output.
`version --debug` shows environment and dependency details for bug reports; it
does not change the logging level.

## Machine output contract

| Rule | Behavior |
| --- | --- |
| Flags | `--json` or `--yaml`. |
| Placement | Put the flag after the command, for example `canfar ps --json`. |
| Conflict | `--json --yaml` exits 2. |
| stdout | Data payload only. |
| stderr | Diagnostics and errors. |
| Unsupported command | Exits 1 with a clear unsupported-machine-output message. |
| Ordering | List ordering is not guaranteed. |
