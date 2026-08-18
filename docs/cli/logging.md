# Logging

The CLI configures Python standard-library logging once at the root entry
point. Human logs use Rich on stderr. File logging is opt-in and writes a
rotating JSON Lines file.

## Controls and precedence

Root controls must precede the command:

```bash
canfar --log-level debug ps
canfar -vvv ps
canfar --log-file ./logs/canfar.jsonl ps
```

| Control | Result |
| --- | --- |
| No CLI control | Use `CANFAR_LOGLEVEL`, or `critical` when it is unset. |
| `-v` | `error`; `-vv` is `warning`; `-vvv` is `info`; `-vvvv` and above are `debug`. |
| `--log-level LEVEL` | Select `critical`, `error`, `warning`, `info`, or `debug`. |
| `--log-file PATH` | Add the rotating JSON Lines file sink. |

Precedence is `--log-level`, repeated `-v`, `CANFAR_LOGLEVEL`, then the
packaged `critical` default. Level names are case-insensitive. A value in
`CANFAR_LOGLEVEL` is validated only when it is the effective source; unknown
`CANFAR_*` variables do not affect logging.

The machine-output option remains owned by the leaf command:

```bash
canfar --log-level debug ps -o json
```

## Streams and machine output

Human command results go to stdout. Logs, warnings, and errors go to stderr.
With `-o json` or `--output yaml`, stdout contains only the selected command
payload; logs and structured diagnostics remain on stderr:

```bash
canfar --log-level debug ps -o json \
  > sessions.json \
  2> diagnostics.log
```

Logging setup warnings use the selected machine format on stderr when a leaf
output mode is present. They never add a banner or log record to the machine
payload on stdout.

At `debug`, Science Platform HTTP hooks log the request method and URL and the
response status and body. These records follow the same stderr/file routing;
do not enable debug logging if response bodies must remain private.

## JSON Lines file sink

File logging is enabled only with `--log-file PATH`. Relative paths resolve
from the current working directory and missing parent directories are created.
There is no default log file and no temporary-file fallback. `-` and an
existing directory are invalid targets.

The sink is UTF-8 JSON Lines with size-based rotation at 10 MiB and ten backup
files. Each event contains:

| Field | Meaning |
| --- | --- |
| `timestamp` | UTC RFC3339 timestamp with millisecond precision and a `Z` suffix. |
| `level` | Logging level such as `INFO` or `ERROR`. |
| `logger` | Logger name such as `canfar.sessions`. |
| `message` | Rendered message. |
| `exception` | Escaped exception or stack text when present. |

One JSON object occupies one physical line. Authentication Record secrets are
masked by their secret types; do not treat log output as a place to expose
credential material.

## Setup diagnostics

| Code | Meaning |
| --- | --- |
| `logging.invalid_env_value` | `CANFAR_LOGLEVEL` is invalid. Setup stops before the command. |
| `logging.invalid_file_path` | `--log-file` is `-` or an existing directory. Setup stops before the command. |
| `logging.file_sink_unavailable` | The file sink cannot initialize, write, or rotate. The command continues with stderr logging. |

The first two are fatal setup errors and exit with status `2`. A file-sink
failure is non-fatal and disables only that sink. In machine mode its warning
is a structured payload on stderr; the command's normal exit status is kept.

## Domain `--debug` options

Root logging controls and command diagnostics are separate. These are the
retained leaf `--debug` meanings:

| Command | Meaning |
| --- | --- |
| `canfar version --debug` | Show environment and dependency details for a bug report. |
| `canfar info SESSION_ID --debug` | Show Session response warnings. |
| `canfar ps --debug` | Show Session response warnings. |
| `canfar create KIND IMAGE --debug` | Print parsed Session request details. |

Other leaves do not use `--debug` as a logging switch. Use a root control,
for example:

```bash
canfar --log-level debug login srcnet
canfar --log-level debug info SESSION_ID --debug
```
