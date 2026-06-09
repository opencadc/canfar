# Authentication and Servers

CANFAR separates identity from routing:

- **Authentication** answers "who am I?"
- **Identity Provider (IDP)** names the organization that authenticates you,
  such as `cadc` or `srcnet`.
- **Science Platform Server** is the endpoint that runs Sessions.
- **Server selection** chooses which compatible Server receives new requests.

`canfar login` handles the full interactive path: choose an IDP, authenticate,
discover compatible Servers, select one, and save the active pair.

## Log in

```bash
canfar login
canfar login cadc
canfar login srcnet
```

Useful options:

| Option | Use |
| --- | --- |
| `--force`, `-f` | Re-authenticate an IDP that already has saved credentials. |
| `--dev` | Include development Servers during discovery. |
| `--timeout`, `-t` | Increase HTTP timeout for login, discovery, and validation. |
| `--debug` | Print debug logs while logging in. |

`canfar auth login` still exists as a deprecated compatibility alias. New docs
and scripts should use `canfar login`.

## Inspect authentication

```bash
canfar auth
canfar auth show
canfar auth ls
```

`canfar auth` defaults to `canfar auth show`.

Use machine output when a script needs stable stdout:

```bash
canfar auth show --json
canfar auth ls --yaml
```

## Switch IDP

```bash
canfar auth use srcnet
canfar auth use cadc
```

When you switch IDP, CANFAR tries to keep routing usable:

1. Reuse the current Server when it belongs to the target IDP.
2. Reuse the remembered Server for that IDP when it is still valid.
3. Auto-select the only compatible Server.
4. Prompt when multiple compatible Servers exist.

## Manage Servers

```bash
canfar server ls
canfar server use canfar
canfar server use ivo://cadc.nrc.ca/skaha
```

Server names are convenient for humans. Server URIs are stable for scripts.

`canfar server ls` shows Servers for the active IDP. If no saved Servers exist
for that IDP, the command runs discovery and stores the results.

## Remove saved auth state

```bash
canfar auth rm srcnet
canfar auth purge --force
```

`auth rm <idp>` removes the Authentication record and Servers associated with
that IDP. Removing the active IDP asks for confirmation unless `--force` is
passed.

`auth purge --force` resets Authentication and Server state while preserving
unrelated configuration such as console and Container Registry settings.

## Python equivalents

```python
import canfar

canfar.login("cadc")
canfar.server.use("ivo://cadc.nrc.ca/skaha")
canfar.authentication.use("srcnet")
```

Python helpers are noninteractive. CLI commands own prompts and human rendering.

## Configuration

The current config shape is versioned with `version: 1`.

```yaml
version: 1
active:
  authentication: cadc
  server: ivo://cadc.nrc.ca/skaha
authentication:
  - idp: cadc
    mode: x509
server:
  - idp: cadc
    name: canfar
    uri: ivo://cadc.nrc.ca/skaha
```

Environment overrides use nested active fields:

```bash
CANFAR_ACTIVE__AUTHENTICATION=srcnet
CANFAR_ACTIVE__SERVER=ivo://example.org/skaha
```

Legacy or unsupported config files are backed up to
`<config-path>.<timestamp>.back` before a default config is written.

## Machine output rules

| Rule | Behavior |
| --- | --- |
| Supported flags | `--json` and `--yaml` |
| Placement | Put the flag after the command that emits data, for example `canfar auth ls --json`. |
| Unsupported placement | `canfar auth --json ls` exits 2. |
| Conflicts | `--json --yaml` exits 2. |
| stdout | Data only in machine mode. |
| stderr | Diagnostics and errors. |
| Unsupported commands | Exit 1 with `machine output not supported for this command yet` and `use default human output for now`. |

Lists have no ordering guarantee. Scripts should select by IDP key, URI,
Session ID, or another stable field.
