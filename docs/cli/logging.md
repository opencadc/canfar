# Logging

CANFAR configures logging only at an explicit application entry point. The CLI
does this once before dispatching a command. Python applications can call
`canfar.configure_logging(...)` themselves; importing `canfar` does not configure
handlers or consoles.

Logging uses Python's standard `logging` library with Rich for human stderr
output, plus an optional rotating JSON Lines file sink.

## CLI controls and precedence

Logging controls are root options, so put them before the command:

```bash
canfar --log-level debug ps
canfar -vvv ps
canfar --log-file ./logs/canfar.jsonl ps
```

The supported controls are:

| Control | Effect |
| --- | --- |
| No CLI control | Use `CANFAR_LOGLEVEL`, or `critical` when it is unset. |
| `-v` | `error` |
| `-vv` | `warning` |
| `-vvv` | `info` |
| `-vvvv` or more | `debug` |
| `--log-level LEVEL` | Select `critical`, `error`, `warning`, `info`, or `debug`. |
| `--log-file PATH` | Add the rotating JSON Lines file sink described below. |

Precedence is:

1. `--log-level`
2. repeated `-v`
3. `CANFAR_LOGLEVEL`
4. the packaged default, `critical`

`--log-level` therefore wins when it is combined with `-v`. Level names are
case-insensitive.

The machine-output flags remain leaf options after the command. For example:

```bash
canfar --log-level debug ps --json
```

The corresponding environment setting is:

```bash
CANFAR_LOGLEVEL=info canfar ps
```

Only the documented CANFAR logging variables affect this policy. Unknown
CANFAR logging variables are ignored.

## Python applications

Call the same runtime seam explicitly in a Python application:

```python
from canfar import configure_logging

configure_logging(loglevel="debug")
```

Calling `configure_logging()` without a level uses `CANFAR_LOGLEVEL`, then the
packaged `critical` default. A Python process that never calls this function
retains the logging configuration chosen by its application.

To add a file sink, pass a `pathlib.Path`:

```python
from pathlib import Path

from canfar import configure_logging

configure_logging(
    loglevel="info",
    log_file=Path("logs/canfar.jsonl"),
)
```

There is no per-`HTTPClient`, `Session`, or `AsyncSession` log-level setting.

## HTTP request and response debug

At `debug` (for example `--log-level debug` or `-vvvv`), every Science Platform
HTTP call logs the request method and full URL, then the response status and
body:

```text
DEBUG  GET https://ws-uv.canfar.net/skaha/v0/session?status=Running
DEBUG  HTTP STATUS CODE -> 200
[{"id":"...","status":"Running",...}]
```

These lines follow the normal logging policy: stderr (and the optional file
sink), never mixed into `--json`/`--yaml` stdout payloads.

## stdout and stderr

CANFAR keeps command data separate from diagnostics:

| Stream | Content |
| --- | --- |
| stdout | Human command results or the selected JSON/YAML data payload. |
| stderr | Rich-oriented logs, warnings, and errors; structured diagnostics in machine mode. |

JSON and YAML stdout remain data-only at every log level. Redirect the streams
independently when a script needs both:

```bash
canfar --log-level debug ps --json \
  > sessions.json \
  2> diagnostics.log
```

In `--json` or `--yaml` mode, logging setup failures and file-sink warnings are
serialized in the selected format on stderr. They never add a banner or log
line to the command payload on stdout.

## Rotating JSON Lines file sink

File logging is opt-in. Use the root option or the Python `Path` argument shown
above. Relative paths resolve from the current working directory, and missing
parent directories are created.

When enabled, events go to both stderr and the file. The file policy is fixed:

- UTF-8 JSON Lines, one object per physical line;
- size-based rotation at 10 MiB;
- 10 backup files; and
- escaped exception and stack text so a record never spans physical lines.

There is no default log file, configuration-file log path, or temporary-file
fallback. In particular, CANFAR does not write `~/.canfar/client.log` unless
that exact path is explicitly requested.

An existing directory and the pseudo-target `-` are invalid file paths. Other
initialization, write, or rollover failures disable only the file sink, keep
stderr logging and command execution active, and emit one
`logging.file_sink_unavailable` warning.

### JSON Lines schema

Every file event contains:

| Field | Required | Meaning |
| --- | --- | --- |
| `timestamp` | Yes | UTC RFC3339 timestamp with `Z` suffix and millisecond precision. |
| `level` | Yes | Logging level name, such as `INFO` or `ERROR`. |
| `logger` | Yes | Logger name, such as `canfar.sessions`. |
| `message` | Yes | Rendered message. |
| `exception` | No | Escaped exception or stack text. |

Example shape:

```json
{"timestamp":"2026-07-11T12:34:56.789Z","level":"INFO","logger":"canfar.sessions","message":"Session request accepted"}
```

Authentication Record secrets use Pydantic `SecretStr` and render as masked
values in Configuration dumps. Do not log raw token or certificate material.

## Stable logging diagnostics

Logging diagnostics use stable dotted-domain codes:

| Code | Behavior and details |
| --- | --- |
| `logging.invalid_env_value` | Fatal setup error. Includes `env_var`, `provided_value`, and `expected`. |
| `logging.invalid_file_path` | Fatal setup error for `-` or an existing directory. Includes the standard `code`, `message`, and `hint` fields. |
| `logging.file_sink_unavailable` | Non-fatal warning for initialization, write, or rollover failure. The command continues with stderr logging; machine mode emits a structured warning on stderr. |

Fatal logging setup errors exit with status 2 before the command executes.
The file-sink warning does not replace the command's normal exit status.

## Domain `--debug` flags

Root logging controls and command diagnostics are separate. These retained
leaf flags have domain-specific meanings and do not select the logging level:

| Command | `--debug` meaning |
| --- | --- |
| `canfar version --debug` | Show environment and dependency details for a bug report. |
| `canfar info SESSION_ID --debug` | Show Session response warnings. |
| `canfar ps --debug` | Show Session response warnings. |
| `canfar create KIND IMAGE --debug` | Print parsed Session request details. |

Logging-only `--debug` flags were removed from `login`, the deprecated
`auth login` alias, `delete`, `events`, `logs`, `open`, `prune`, and `stats`.
Use a root control instead:

```bash
canfar --log-level debug login cadc --force
canfar --log-level debug info abc123 --debug
```

The second example requests both debug-level logs and the independent Session
response-anomaly details.
