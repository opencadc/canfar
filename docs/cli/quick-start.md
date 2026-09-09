# CLI quickstart

This walkthrough logs in, launches a Session, checks it, opens it, and removes
it. Replace `SESSION_ID` with the ID printed by `canfar create` or `canfar ps`.

## Install and log in

[Install the client](../client/get-started.md#install) first. These examples describe the unreleased
`feat/interfaces` interface; follow the installation guide to choose a
compatible environment.

```bash
canfar login cadc
```

Use SRCNet OIDC instead when that is your Identity Provider:

```bash
canfar login srcnet
```

Inspect the active Authentication and available Servers:

```bash
canfar auth show
canfar server ls
```

For the OIDC Device Authorization steps, see [Authentication and Servers](authentication-contexts.md).

## Optional data check

Use a configured Storage Identifier and an absolute path:

```bash
canfar data ls -lh arc:/home/user
```

See [Data commands](data.md) for copy, recursive-copy, and cross-source
workflows.

## Create a notebook Session

```bash
canfar create notebook skaha/astroml:latest
```

The image shorthand is normalized to the CANFAR Container Registry. Fixed
resources are optional:

```bash
canfar create notebook skaha/astroml:latest --cpu 4 --memory 16
```

For a headless command, put the command delimiter before the container
command. Every token after `--` belongs to that command:

```bash
canfar create headless skaha/terminal:1.1.2 -- python /arc/projects/demo/run.py
```

## Check and open the Session

```bash
canfar ps
canfar info SESSION_ID
canfar open SESSION_ID
```

`ps` shows `Pending` and `Running` Sessions by default. Use `--all` for every
status, or `-o json` when a script needs a data-only payload:

```bash
canfar ps --all
canfar ps -o json
```

`ps -q` is a human-only ID shortcut and can include the active-Server banner;
use machine output when passing results between tools.

Inspect startup events or logs when a Session is not ready:

```bash
canfar events SESSION_ID
canfar logs SESSION_ID
```

## Remove the Session

```bash
canfar delete SESSION_ID
```

The command asks for confirmation. Use `--force` in a controlled script:

```bash
canfar delete SESSION_ID --force
```

## Troubleshooting

Put logging controls before the command:

```bash
canfar --log-level debug login cadc --force
canfar --log-level debug ps
```

See [Logging](logging.md) for level precedence, stderr routing, and the
optional JSON Lines file sink. See the [CLI reference](cli-help.md) for every
leaf and option.
