# CLI Reference

The Canfar CLI provides a comprehensive command-line interface for interacting with the Science Platform. This reference covers all available commands and their options.

!!! info "Getting Started"
    The CLI can be accessed using the `canfar` command in your environment:
    ```bash
    canfar --help
    ```

## Main Command

```bash
canfar [OPTIONS] COMMAND [ARGS]...
```

**Description:** Command Line Interface for Science Platform.

### Global Options

| Option | Description |
|--------|-------------|
| `--install-completion` | Install completion for the current shell |
| `--show-completion` | Show completion for the current shell, to copy it or customize the installation |
| `--help` | Show help message and exit |

!!! tip "Shell Completion"
    Enable shell completion for a better CLI experience by running:
    ```bash
    canfar --install-completion
    ```

---

## 🔐 Authentication Commands

### `canfar auth`

Authenticate with Science Platform.

#### `canfar auth login`

Login to Science Platform with automatic server discovery.

```bash
canfar auth login [OPTIONS]
```

**Description:** This command guides you through the authentication process, automatically discovering the upstream server and choosing the appropriate authentication method based on the server's configuration.

##### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force` | Flag | - | Force re-authentication |
| `--debug` | Flag | - | Enable debug logging |
| `--dead` | Flag | - | Include dead servers in discovery |
| `--dev` | Flag | - | Include dev servers in discovery |
| `--details` | Flag | - | Include server details in discovery |
| `--timeout`, `-t` | INTEGER | 2 | Timeout for server response |
| `--discovery-url` | TEXT | `https://ska-iam.stfc.ac.uk/.well-known/openid-configuration` | OIDC Discovery URL |

!!! example "Basic Login"
    ```bash
    canfar auth login
    ```

!!! example "Login with Debug Information"
    ```bash
    canfar auth login --debug --details
    ```

#### `canfar auth list` / `canfar auth ls`

Show all available authentication contexts.

```bash
canfar auth list [OPTIONS]
```

!!! example
    ```bash
    canfar auth list
    ```

#### `canfar auth switch` / `canfar auth use`

Switch the active authentication context.

```bash
canfar auth switch CONTEXT
```

**Arguments:**
- `CONTEXT` (required): The name of the context to activate

!!! example
    ```bash
    canfar auth switch production
    ```

#### `canfar auth remove` / `canfar auth rm`

Remove a specific authentication context.

```bash
canfar auth remove CONTEXT
```

**Arguments:**
- `CONTEXT` (required): The name of the context to remove

!!! warning "Permanent Action"
    This action permanently removes the authentication context and cannot be undone.

#### `canfar auth purge`

Remove all authentication contexts.

```bash
canfar auth purge [OPTIONS]
```

##### Options

| Option | Description |
|--------|-------------|
| `--yes`, `-y` | Skip confirmation prompt |

!!! danger "Destructive Action"
    This command removes ALL authentication contexts. Use with caution!

---

## 🚀 Session Management Commands

### `canfar create`

Create a new session on the Science Platform.

```bash
canfar create [OPTIONS] desktop|notebook|carta|headless|firefly|desktop-app|contributed IMAGE [-- CMD [ARGS]...]
```

**Arguments:**
- `KIND` (required): Session type - one of: `desktop`, `notebook`, `carta`, `headless`, `firefly`, `desktop-app`, `contributed`
- `IMAGE` (required): Container image to use
- `CMD [ARGS]...` (optional): Runtime command and arguments

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--name` | `-n` | TEXT | Auto-generated | Name of the session |
| `--cpu` | `-c` | INTEGER | 1 | Number of CPU cores |
| `--memory` | `-m` | INTEGER | 2 | Amount of RAM in GB |
| `--gpu` | `-g` | INTEGER | None | Number of GPUs |
| `--env` | `-e` | TEXT | None | Environment variables (e.g., `--env KEY=VALUE`) |
| `--replicas` | `-r` | INTEGER | 1 | Number of replicas to create |
| `--debug` | - | Flag | - | Enable debug logging |
| `--dry-run` | - | Flag | - | Perform a dry run without creating the session |

!!! example "Create a Jupyter Notebook"
    ```bash
    canfar create --cpu 4 --memory 8 notebook skaha/astroml-notebook:latest
    ```

!!! example "Create a Headless Session with Custom Command"
    ```bash
    canfar create headless skaha/terminal:1.1.2 -- env
    ```

### `canfar ps`

Show running sessions.

```bash
canfar ps [OPTIONS]
```

#### Options

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--all` | `-a` | Flag | Show all sessions (default shows just running) |
| `--quiet` | `-q` | Flag | Only show session IDs |
| `--kind` | `-k` | Choice | Filter by session kind: `desktop`, `notebook`, `carta`, `headless`, `firefly`, `desktop-app`, `contributed` |
| `--status` | `-s` | Choice | Filter by status: `Pending`, `Running`, `Terminating`, `Succeeded`, `Error`, `Failed` |
| `--debug` | - | Flag | Enable debug logging |

!!! example "List All Sessions"
    ```bash
    canfar ps --all
    ```

!!! example "List Only Notebook Sessions"
    ```bash
    canfar ps --kind notebook
    ```

### `canfar events`

Show session events for debugging and monitoring.

```bash
canfar events [OPTIONS] SESSION_IDS...
```

**Arguments:**
- `SESSION_IDS...` (required): One or more session IDs

#### Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging |

!!! example
    ```bash
    canfar events abc123 def456
    ```

### `canfar info`

Show detailed information about sessions.

```bash
canfar info [OPTIONS] SESSION_IDS...
```

**Arguments:**
- `SESSION_IDS...` (required): One or more session IDs

#### Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging |

!!! example
    ```bash
    canfar info abc123
    ```

### `canfar open`

Open sessions in a web browser.

```bash
canfar open [OPTIONS] SESSION_IDS...
```

**Arguments:**
- `SESSION_IDS...` (required): One or more session IDs

#### Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging |

!!! tip "Browser Integration"
    This command automatically opens the session URLs in your default web browser.

!!! example
    ```bash
    canfar open abc123 def456
    ```

### `canfar logs`

Show session logs for troubleshooting.

```bash
canfar logs [OPTIONS] SESSION_IDS...
```

**Arguments:**
- `SESSION_IDS...` (required): One or more session IDs

#### Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging |

!!! example
    ```bash
    canfar logs abc123
    ```

### `canfar delete`

Delete one or more sessions.

```bash
canfar delete [OPTIONS] SESSION_IDS...
```

**Arguments:**
- `SESSION_IDS...` (required): One or more session IDs to delete

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--force` | `-f` | Force deletion without confirmation |
| `--debug` | - | Enable debug logging |

!!! warning "Permanent Action"
    Deleted sessions cannot be recovered. Use `--force` to skip confirmation prompts.

!!! example "Delete with Confirmation"
    ```bash
    canfar delete abc123
    ```

!!! example "Force Delete Multiple Sessions"
    ```bash
    canfar delete abc123 def456 --force
    ```

### `canfar prune`

Prune sessions by criteria for bulk cleanup.

```bash
canfar prune [OPTIONS] NAME KIND STATUS
```

**Arguments:**
- `NAME` (required): Prefix to match session names
- `KIND` (optional): Session kind - default: `headless` (one of: `desktop`, `notebook`, `carta`, `headless`, `firefly`, `desktop-app`, `contributed`)
- `STATUS` (optional): Session status - default: `Succeeded` (one of: `Pending`, `Running`, `Terminating`, `Succeeded`, `Error`, `Failed`)

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--debug` | - | Enable debug logging |
| `--help` | `-h` | Show help message and exit |

!!! example "Prune Completed Headless Sessions"
    ```bash
    canfar prune "test-" headless Running
    ```

!!! tip "Bulk Cleanup"
    Use prune to clean up multiple sessions that match specific criteria, especially useful for automated workflows.

---

## 📊 Cluster Information Commands

### `canfar stats`

Show cluster statistics and resource usage.

```bash
canfar stats [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging |

!!! example
    ```bash
    canfar stats
    ```

!!! info "Resource Monitoring"
    This command provides insights into cluster resource usage, helping you understand available capacity.

---

## ⚙️ Client Configuration Commands

### `canfar config`

Manage client configuration settings.

#### `canfar config show` / `canfar config list` / `canfar config ls`

Display the current configuration.

```bash
canfar config show [OPTIONS]
```

!!! example
    ```bash
    canfar config ls
    ```

#### `canfar config path`

Display the path to the configuration file.

```bash
canfar config path [OPTIONS]
```

!!! example
    ```bash
    canfar config path
    ```

!!! tip "Configuration Location"
    Use this command to find where your configuration file is stored for manual editing if needed.

### `canfar version`

View client version and system information.

```bash
canfar version [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--debug` / `--no-debug` | `--no-debug` | Show detailed information for bug reports |

!!! example "Basic Version Info"
    ```bash
    canfar version
    ```

!!! example "Detailed Debug Information"
    ```bash
    canfar version --debug
    ```
