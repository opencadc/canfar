# CLI Reference

The CLI provides a comprehensive command-line interface for interacting with the CANFAR Science Platform. This reference covers all available commands and their options.

!!! info "Getting Started"
The CLI can be accessed using the `canfar` command in your environment:
`bash
    canfar --help
    `

## Main Command

```bash
canfar [OPTIONS] COMMAND [ARGS]...
```

**Description:** Command Line Interface for Science Platform.

### Global Options

| Option                 | Description                                                                     |
| ---------------------- | ------------------------------------------------------------------------------- |
| `--install-completion` | Install completion for the current shell                                        |
| `--show-completion`    | Show completion for the current shell, to copy it or customize the installation |
| `--help`               | Show help message and exit                                                      |

!!! tip "Shell Completion"
Enable shell completion for a better CLI experience by running:
`bash
    canfar --install-completion
    `

---

## Authentication

### `canfar auth`

This command group provides tools for managing authentication contexts for connecting to Science Platform servers.

#### `canfar auth login`

Login to Science Platform with automatic server discovery.

```bash
canfar auth login [OPTIONS]
```

**Description:** This command guides you through the authentication process, automatically discovering the upstream server and choosing the appropriate authentication method based on the server's configuration.

##### Options

| Option            | Type    | Default                                                       | Description                         |
| ----------------- | ------- | ------------------------------------------------------------- | ----------------------------------- |
| `--force`         | Flag    | -                                                             | Force re-authentication             |
| `--debug`         | Flag    | -                                                             | Enable debug logging                |
| `--dead`          | Flag    | -                                                             | Include dead servers in discovery   |
| `--dev`           | Flag    | -                                                             | Include dev servers in discovery    |
| `--details`       | Flag    | -                                                             | Include server details in discovery |
| `--timeout`, `-t` | INTEGER | 2                                                             | Timeout for server response         |
| `--discovery-url` | TEXT    | `https://ska-iam.stfc.ac.uk/.well-known/openid-configuration` | OIDC Discovery URL                  |

!!! example "Basic Login"
`bash
    canfar auth login
    `

!!! example "Login with Debug Information"
`bash
    canfar auth login --debug --details
    `

#### `canfar auth list` / `canfar auth ls`

Shows all available authentication contexts.

```bash
canfar auth list [OPTIONS]
```

#### `canfar auth switch` / `canfar auth use`

Switch the active authentication context.

```bash
canfar auth switch CONTEXT
```

**Arguments:**

- `CONTEXT` (required): The name of the context to activate

!!! example
`bash
    canfar auth switch SRCnet-Sweden
    `

#### `canfar auth remove` / `canfar auth rm`

Remove a specific authentication context from the configuration.

```bash
canfar auth remove CONTEXT
```

**Arguments:**

- `CONTEXT` (required): The name of the context to remove

!!! warning "Permanent Action"
This action permanently removes the authentication context and cannot be undone.

#### `canfar auth purge`

Remove all authentication contexts and credentials from the configuration.

```bash
canfar auth purge [OPTIONS]
```

##### Options

| Option        | Description              |
| ------------- | ------------------------ |
| `--yes`, `-y` | Skip confirmation prompt |

!!! danger "Destructive Action"
This command removes ALL authentication contexts. Use with caution!

---

## Session Management

### `canfar create`

Create a new session on the Science Platform.

```bash
canfar create [OPTIONS] KIND IMAGE [-- CMD [ARGS]...]
```

!!! note "Passing Commands & Arguments"

    ```bash
    canfar create headless skaha/terminal:1.1.2 -- python3 /path/to/script.py --arg1
    ```
    In this example, `python3` is the command and `/path/to/script.py --arg1` are the arguments.

    !!! warning ""

        - If you need to pass arguments to the command, you must use the `--` separator.
        - If you don’t supply a `CMD`, the `--` is not necessary.

**Arguments:**

- `KIND` (required): Session type - one of: `desktop`, `notebook`, `carta`, `headless`, `firefly`, `contributed`
- `IMAGE` (required): Container image to use
- `CMD [ARGS]...` (optional): Runtime command and arguments

#### Options

| Option       | Short | Type    | Default        | Description                                                                |
| ------------ | ----- | ------- | -------------- | -------------------------------------------------------------------------- |
| `--name`     | `-n`  | TEXT    | Auto-generated | Name of the session                                                        |
| `--cpu`      | `-c`  | INTEGER | flexible       | Number of CPU cores (optional - uses flexible allocation if not specified) |
| `--memory`   | `-m`  | INTEGER | flexible       | Amount of RAM in GB (optional - uses flexible allocation if not specified) |
| `--gpu`      | `-g`  | INTEGER | None           | Number of GPUs                                                             |
| `--env`      | `-e`  | TEXT    | None           | Environment variables (e.g., `--env KEY=VALUE`)                            |
| `--replicas` | `-r`  | INTEGER | 1              | Number of replicas to create                                               |
| `--debug`    | -     | Flag    | -              | Enable debug logging                                                       |
| `--dry-run`  | -     | Flag    | -              | Dry run. Parse parameters and exit                                         |

!!! example "Create a Flexible Notebook Session (Default)"
`bash
    # Uses flexible resource allocation - adapts to user load
    canfar create notebook skaha/astroml:latest
    `

!!! example "Create a Fixed Resource Notebook Session"
`bash
    # Uses fixed resource allocation - guaranteed resources
    canfar create --cpu 4 --memory 8 notebook skaha/astroml:latest
    `

!!! example "Create a Headless Session with Command & Arguments"
`bash
    canfar create headless skaha/terminal:1.1.2 -- python3 /path/to/script.py --arg1 --arg2
    `

!!! example "Create Replicated Headless Sessions"
``bash
    # Create 10 headless replicas running the `env` command
    canfar create --replicas 10 headless skaha/terminal:1.1.2 -- env
    ``

#### Resource Allocation Modes

CANFAR Science Platform supports two resource allocation modes, see [platform concepts](../platform/concepts.md#resource-allocation-modes) for more information.

### `canfar ps`

Show running sessions.

```bash
canfar ps [OPTIONS]
```

#### Options

| Option     | Short | Type   | Description                                                                                                 |
| ---------- | ----- | ------ | ----------------------------------------------------------------------------------------------------------- |
| `--all`    | `-a`  | Flag   | Show all sessions (default shows just running)                                                              |
| `--quiet`  | `-q`  | Flag   | Only show session IDs                                                                                       |
| `--kind`   | `-k`  | Choice | Filter by session kind: `desktop`, `notebook`, `carta`, `headless`, `firefly`, `desktop-app`, `contributed` |
| `--status` | `-s`  | Choice | Filter by status: `Pending`, `Running`, `Terminating`, `Succeeded`, `Error`, `Failed`                       |
| `--debug`  | -     | Flag   | Enable debug logging                                                                                        |

!!! example "List All Sessions"
`bash
    canfar ps --all
    `

!!! example "List Only Notebook Sessions"
`bash
    canfar ps --kind notebook
    `

### `canfar events`

Show session events for debugging and monitoring.

```bash
canfar events [OPTIONS] SESSION_IDS...
```

**Arguments:**

- `SESSION_IDS...` (required): One or more session IDs

#### Options

| Option    | Description          |
| --------- | -------------------- |
| `--debug` | Enable debug logging |

!!! example
`bash
    canfar events abc123 def456
    `

### `canfar info`

Show detailed information about sessions.

```bash
canfar info [OPTIONS] SESSION_IDS...
```

**Arguments:**

- `SESSION_IDS...` (required): One or more session IDs

#### Options

| Option    | Description          |
| --------- | -------------------- |
| `--debug` | Enable debug logging |

!!! example
`bash
    canfar info abc123
    `

### `canfar open`

Open sessions in a web browser.

```bash
canfar open [OPTIONS] SESSION_IDS...
```

**Arguments:**

- `SESSION_IDS...` (required): One or more session IDs

#### Options

| Option    | Description          |
| --------- | -------------------- |
| `--debug` | Enable debug logging |

!!! tip "Browser Integration"
This command automatically opens the session URLs in your default web browser.

!!! example
`bash
    canfar open abc123 def456
    `

### `canfar logs`

Show session logs for troubleshooting.

```bash
canfar logs [OPTIONS] SESSION_IDS...
```

**Arguments:**

- `SESSION_IDS...` (required): One or more session IDs

#### Options

| Option    | Description          |
| --------- | -------------------- |
| `--debug` | Enable debug logging |

!!! example
`bash
    canfar logs abc123
    `

### `canfar delete`

Delete one or more sessions.

```bash
canfar delete [OPTIONS] SESSION_IDS...
```

**Arguments:**

- `SESSION_IDS...` (required): One or more session IDs to delete

#### Options

| Option    | Short | Description                         |
| --------- | ----- | ----------------------------------- |
| `--force` | `-f`  | Force deletion without confirmation |
| `--debug` | -     | Enable debug logging                |

!!! warning "Permanent Action"
Deleted sessions cannot be recovered. Use `--force` to skip confirmation prompts.

!!! example "Delete with Confirmation"
`bash
    canfar delete abc123
    `

!!! example "Force Delete Multiple Sessions"
`bash
    canfar delete abc123 def456 --force
    `

### `canfar prune`

Prune sessions by criteria for bulk cleanup.

```bash
canfar prune [OPTIONS] PREFIX KIND STATUS
```

**Arguments:**

- `PREFIX` (required): Prefix to match session names; regex is used if metacharacters are present
- `KIND` (optional): Session kind - default: `headless` (one of: `desktop`, `notebook`, `carta`, `headless`, `firefly`, `desktop-app`, `contributed`)
- `STATUS` (optional): Session status - default: `Succeeded` (one of: `Pending`, `Running`, `Terminating`, `Succeeded`, `Error`, `Failed`)

#### Options

| Option    | Short | Description                |
| --------- | ----- | -------------------------- |
| `--debug` | -     | Enable debug logging       |
| `--help`  | `-h`  | Show help message and exit |

!!! example "Prune Completed Headless Sessions"
`bash
    canfar prune "test-" headless Running
    canfar prune ".*-was-" notebook Running  # regex because of metacharacters
    `

!!! tip "Bulk Cleanup"
Use prune to clean up multiple sessions that match specific criteria, especially useful for automated workflows.

---

## Cluster Info

### `canfar stats`

Show cluster statistics and resource usage.

```bash
canfar stats [OPTIONS]
```

#### Options

| Option    | Description          |
| --------- | -------------------- |
| `--debug` | Enable debug logging |

!!! example
`bash
    canfar stats
    `

!!! info "Resource Monitoring"
This command provides insights into cluster resource usage, helping you understand available capacity.

---

## Client Configuration

### `canfar config`

Manage client configuration settings.

#### `canfar config show` / `canfar config list` / `canfar config ls`

Display the current configuration.

```bash
canfar config show [OPTIONS]
```

!!! example
`bash
    canfar config ls
    `

#### `canfar config path`

Display the path to the configuration file.

```bash
canfar config path [OPTIONS]
```

!!! example
`bash
    canfar config path
    `

!!! tip "Configuration Location"
Use this command to find where your configuration file is stored for manual editing if needed.

#### `canfar config get`

Get a single configuration value by dotted path.

```bash
canfar config get PATH
```

!!! example
`bash
    canfar config get console.width
    `

#### `canfar config set`

Set a single configuration value by dotted path (value is parsed as YAML).

```bash
canfar config set PATH VALUE
```

!!! example
`bash
    canfar config set console.width 130
    `

### `canfar version`

View client version and system information.

```bash
canfar version [OPTIONS]
```

#### Options

| Option                   | Default      | Description                               |
| ------------------------ | ------------ | ----------------------------------------- |
| `--debug` / `--no-debug` | `--no-debug` | Show detailed information for bug reports |

!!! example "Basic Version Info"
`bash
    canfar version
    `

!!! example "Detailed Debug Information"
`bash
    canfar version --debug
    `

---

## File Management (VOSpace)

The `canfar storage` command group provides comprehensive file management capabilities for VOSpace, CANFAR's persistent storage system. These commands use the same authentication context as session management, providing a unified experience.

!!! info "VOSpace Paths"
VOSpace paths use the `vos:` prefix, e.g., `vos:/data/file.txt` or `vos:` for the root directory.

### `canfar storage ls`

List VOSpace directory contents.

```bash
canfar storage ls [OPTIONS] URI
```

**Arguments:**

- `URI` (required): VOSpace path to list (e.g., `vos:`, `vos:/dir`, `vos:/data/*.fits`)

#### Options

| Option      | Short | Description                                             |
| ----------- | ----- | ------------------------------------------------------- |
| `--long`    | `-l`  | Verbose listing with permissions, owner, size, and date |
| `--group`   | `-g`  | Display group read/write information                    |
| `--human`   | `-h`  | Make sizes human readable (K, M, G, T)                  |
| `--Size`    | `-S`  | Sort files by size                                      |
| `--reverse` | `-r`  | Reverse the sort order                                  |
| `--time`    | `-t`  | Sort by time copied to VOSpace                          |
| `--debug`   | -     | Enable debug logging                                    |

!!! example "List Root Directory"
`bash
    canfar vos ls vos:
    `

!!! example "Long Listing with Human-Readable Sizes"
`bash
    canfar vos ls -lh vos:/data/
    `

!!! example "List FITS Files Sorted by Size"
`bash
    canfar storage ls -lhS vos:/data/*.fits
    `

### `canfar storage cp`

Copy files to and from VOSpace.

```bash
canfar storage cp [OPTIONS] SOURCE... DESTINATION
```

**Arguments:**

- `SOURCE...` (required): Source file(s)/directory to copy from (supports wildcards)
- `DESTINATION` (required): Destination file/directory to copy to

#### Options

| Option           | Short | Description                                       |
| ---------------- | ----- | ------------------------------------------------- |
| `--exclude`      | -     | Skip files matching pattern (overrides include)   |
| `--include`      | -     | Only copy files matching pattern                  |
| `--interrogate`  | `-i`  | Ask before overwriting files                      |
| `--follow-links` | `-L`  | Follow symbolic links                             |
| `--ignore`       | -     | Ignore errors and continue with recursive copy    |
| `--head`         | -     | Copy only the headers of a FITS file from VOSpace |
| `--debug`        | -     | Enable debug logging                              |

!!! example "Upload a File"
`bash
    canfar storage cp myfile.txt vos:/data/
    `

!!! example "Download Files with Wildcard"
`bash
    canfar storage cp vos:/data/*.fits ./local_dir/
    `

!!! example "Copy with Confirmation"
`bash
    canfar storage cp -i local_dir/ vos:/backup/
    `

!!! example "Copy FITS Header Only"
`bash
    canfar storage cp --head vos:/data/image.fits ./header.txt
    `

### `canfar storage rm`

Remove VOSpace files or directories.

```bash
canfar storage rm [OPTIONS] NODE...
```

**Arguments:**

- `NODE...` (required): VOSpace file(s) or directory to delete

#### Options

| Option        | Short | Description                        |
| ------------- | ----- | ---------------------------------- |
| `--recursive` | `-R`  | Delete directory even if not empty |
| `--debug`     | -     | Enable debug logging               |

!!! warning "Permanent Action"
Deleted files cannot be recovered. Use with caution!

!!! example "Delete a File"
`bash
    canfar storage rm vos:/data/file.txt
    `

!!! example "Delete a Directory Recursively"
`bash
    canfar storage rm -R vos:/data/old_dir/
    `

### `canfar storage mkdir`

Create a new VOSpace directory (ContainerNode).

```bash
canfar storage mkdir [OPTIONS] CONTAINER_NODE
```

**Arguments:**

- `CONTAINER_NODE` (required): VOSpace directory path to create

#### Options

| Option      | Short | Description                                 |
| ----------- | ----- | ------------------------------------------- |
| `--parents` | `-p`  | Create intermediate directories as required |
| `--debug`   | -     | Enable debug logging                        |

!!! example "Create a Directory"
`bash
    canfar storage mkdir vos:/data/new_dir
    `

!!! example "Create Nested Directories"
`bash
    canfar storage mkdir -p vos:/data/path/to/new_dir
    `

### `canfar storage mv`

Move or rename a VOSpace node.

```bash
canfar storage mv [OPTIONS] SOURCE DESTINATION
```

**Arguments:**

- `SOURCE` (required): VOSpace node to move
- `DESTINATION` (required): VOSpace destination path

#### Options

| Option    | Description          |
| --------- | -------------------- |
| `--debug` | Enable debug logging |

!!! example "Rename a File"
`bash
    canfar vos mv vos:/data/old.txt vos:/data/new.txt
    `

!!! example "Move to Another Directory"
`bash
    canfar storage mv vos:/data/file.txt vos:/archive/
    `
