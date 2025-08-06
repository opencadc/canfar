# CLI Reference

The Skaha CLI provides a comprehensive command-line interface for interacting with the Science Platform. This reference covers all available commands and their options.

!!! info "Getting Started"
    The CLI can be accessed using the `skaha` command in your uv environment:
    ```bash
    uv run skaha --help
    ```

## Main Command

```bash
skaha [OPTIONS] COMMAND [ARGS]...
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
    skaha --install-completion
    ```

---

## 🔐 Authentication Commands

### `skaha auth`

Authenticate with Science Platform.

#### `skaha auth login`

Login to Science Platform with automatic server discovery.

```bash
skaha auth login [OPTIONS]
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
| `--discovery-url`, `-d` | TEXT | `https://ska-iam.stfc.ac.uk/.well-known/openid-configuration` | OIDC Discovery URL |

!!! example "Basic Login"
    ```bash
    skaha auth login
    ```

!!! example "Login with Debug Information"
    ```bash
    skaha auth login --debug --details
    ```

#### `skaha auth list` / `skaha auth ls`

Show all available authentication contexts.

```bash
skaha auth list [OPTIONS]
```

!!! example
    ```bash
    skaha auth list
    ```

#### `skaha auth switch` / `skaha auth use`

Switch the active authentication context.

```bash
skaha auth switch CONTEXT
```

**Arguments:**
- `CONTEXT` (required): The name of the context to activate

!!! example
    ```bash
    skaha auth switch production
    ```

#### `skaha auth remove` / `skaha auth rm`

Remove a specific authentication context.

```bash
skaha auth remove CONTEXT
```

**Arguments:**
- `CONTEXT` (required): The name of the context to remove

!!! warning "Permanent Action"
    This action permanently removes the authentication context and cannot be undone.

#### `skaha auth purge`

Remove all authentication contexts.

```bash
skaha auth purge [OPTIONS]
```

##### Options

| Option | Description |
|--------|-------------|
| `--yes`, `-y` | Skip confirmation prompt |

!!! danger "Destructive Action"
    This command removes ALL authentication contexts. Use with caution!

---

## 🚀 Session Management Commands

### `skaha create`

Create a new session on the Science Platform.

```bash
skaha create [OPTIONS] KIND IMAGE [-- CMD [ARGS]...]
```

**Arguments:**
- `KIND` (required): Session type - one of: `desktop`, `notebook`, `carta`, `headless`, `firefly`
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
    skaha create --cpu 4 -m 8notebook skaha/scipy-notebook:latest
    ```

!!! example "Create a Headless Session with Custom Command"
    ```bash
    uv run skaha create headless skaha/terminal:1.1.2 -- env
    ```

### `skaha ps`

Show running sessions.

```bash
skaha ps [OPTIONS]
```

#### Options

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--all` | `-a` | Flag | Show all sessions (default shows just running) |
| `--quiet` | `-q` | Flag | Only show session IDs |
| `--kind` | `-k` | Choice | Filter by session kind: `desktop`, `notebook`, `carta`, `headless`, `firefly` |
| `--status` | `-s` | Choice | Filter by status: `Pending`, `Running`, `Terminating`, `Succeeded`, `Error` |
| `--debug` | - | Flag | Enable debug logging |

!!! example "List All Sessions"
    ```bash
    skaha ps --all
    ```

!!! example "List Only Notebook Sessions"
    ```bash
    skaha ps --kind notebook
    ```

### `skaha events`

Show session events for debugging and monitoring.

```bash
skaha events [OPTIONS] SESSION_IDS...
```

**Arguments:**
- `SESSION_IDS...` (required): One or more session IDs

#### Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging |

!!! example
    ```bash
    skaha events abc123 def456
    ```

### `skaha info`

Show detailed information about sessions.

```bash
skaha info [OPTIONS] SESSION_IDS...
```

**Arguments:**
- `SESSION_IDS...` (required): One or more session IDs

#### Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging |

!!! example
    ```bash
    skaha info abc123
    ```

### `skaha open`

Open sessions in a web browser.

```bash
skaha open [OPTIONS] SESSION_IDS...
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
    skaha open abc123 def456
    ```

### `skaha logs`

Show session logs for troubleshooting.

```bash
skaha logs [OPTIONS] SESSION_IDS...
```

**Arguments:**
- `SESSION_IDS...` (required): One or more session IDs

#### Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging |

!!! example
    ```bash
    skaha logs abc123
    ```

### `skaha delete`

Delete one or more sessions.

```bash
skaha delete [OPTIONS] SESSION_IDS...
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
    skaha delete abc123
    ```

!!! example "Force Delete Multiple Sessions"
    ```bash
    skaha delete abc123 def456 --force
    ```

### `skaha prune`

Prune sessions by criteria for bulk cleanup.

```bash
skaha prune [OPTIONS] NAME [KIND] [STATUS]
```

**Arguments:**
- `NAME` (required): Prefix to match session names
- `KIND` (optional): Session kind - default: `headless`
- `STATUS` (optional): Session status - default: `Succeeded`

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--debug` | - | Enable debug logging |
| `--help` | `-h` | Show help message and exit |

!!! example "Prune Completed Headless Sessions"
    ```bash
    skaha prune "test-" headless Running
    ```

!!! tip "Bulk Cleanup"
    Use prune to clean up multiple sessions that match specific criteria, especially useful for automated workflows.

---

## 📊 Cluster Information Commands

### `skaha stats`

Show cluster statistics and resource usage.

```bash
skaha stats [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging |

!!! example
    ```bash
    skaha stats
    ```

!!! info "Resource Monitoring"
    This command provides insights into cluster resource usage, helping you understand available capacity.

---

## ⚙️ Client Configuration Commands

### `skaha config`

Manage client configuration settings.

#### `skaha config show` / `skaha config list` / `skaha config ls`

Display the current configuration.

```bash
skaha config show [OPTIONS]
```

!!! example
    ```bash
    skaha config ls
    ```

#### `skaha config path`

Display the path to the configuration file.

```bash
skaha config path [OPTIONS]
```

!!! example
    ```bash
    skaha config path
    ```

!!! tip "Configuration Location"
    Use this command to find where your configuration file is stored for manual editing if needed.

### `skaha version`

View client version and system information.

```bash
skaha version [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--debug` / `--no-debug` | `--no-debug` | Show detailed information for bug reports |

!!! example "Basic Version Info"
    ```bash
    skaha version
    ```

!!! example "Detailed Debug Information"
    ```bash
    skaha version --debug
    ```
