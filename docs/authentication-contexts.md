# Authentication Guide

Skaha is designed to connect to multiple Science Platform servers around the world. This guide covers everything you need to know about authentication, from basic setup to advanced scenarios.

## Authentication Overview

Skaha uses an **Authentication Context** system to manage connections to different Science Platform servers. This system supports multiple authentication methods and makes it easy to switch between servers.

### What is an Authentication Context?

Think of an authentication context (*context* for short) as a saved profile that contains:

- **Server information** (URL, capabilities)
- **Authentication credentials** (X.509 certificate, OIDC tokens, etc.)
- **User preferences** for that specific server

When you use Skaha, one context is always **active**, and all commands and API calls are directed to that server.

### Authentication Methods

Skaha supports several authentication methods:

!!! info "Authentication Methods"
    - **X.509 Certificates** - Most common, uses `.pem` certificate files
    - **OIDC Tokens** - OpenID Connect for modern authentication flows
    - **Bearer Tokens** - Direct token authentication for API access

!!! tip "Automatic Configuration"
    Starting with v1.7, Skaha automatically configures the appropriate authentication method based on the server's capabilities and your configuration.

---

## CLI Authentication Management

The Skaha CLI provides comprehensive commands for managing your authentication contexts.

### Initial Login (`skaha auth login`)

The `login` command is your starting point for connecting to any Science Platform server:

```bash
skaha auth login
```

**What happens during login:**

1. **Server Discovery** - Automatically finds available Science Platform servers worldwide
2. **Server Selection** - Interactive prompt to choose your target server
3. **Authentication Flow** - Guides you through the server's authentication method
4. **Context Creation** - Saves your credentials and server configuration
5. **Activation** - Sets the new context as active for immediate use

!!! example "Login Options"
    ```bash
    # Basic login with server discovery
    skaha auth login

    # Include development/testing servers
    skaha auth login --dev

    # Include non-responsive servers in discovery
    skaha auth login --dead

    # Show detailed server information during selection
    skaha auth login --details

    # Force re-authentication for existing context
    skaha auth login --force
    ```

### Managing Multiple Contexts

Once you have one or more authentication contexts, you can easily manage them:

#### Listing Contexts (`skaha auth list`)

View all your saved authentication contexts:

```bash
skaha auth list
```

**Example Output:**
```
                  Available Authentication Contexts                  
                                                                     
  Active   Name          Auth Mode   Server URL                      
 ─────────────────────────────────────────────────────────────────── 
    ✅     CADC-CANFAR     x509      https://ws-uv.canfar.net/skaha  
                                                                     
           SRCnet-Sweden   oidc      https://services.swesrc.chalmers.se/skaha
```

The active context (marked with ✅) determines where your commands are sent.

#### Switching Contexts (`skaha auth switch`)

Switch between your saved contexts safely:

```bash
skaha auth switch <CONTEXT_NAME>
```

!!! example "Switching Examples"
    ```bash
    # Switch to a different server
    skaha auth switch SRCnet-Sweden

    # Switch back to CANFAR
    skaha auth use CADC-CANFAR
    ```

All subsequent commands will use the newly active context.

#### Removing Contexts (`skaha auth remove`)

Remove contexts you no longer need:

```bash
skaha auth remove <CONTEXT_NAME>
```

!!! warning "Safety Features"
    - You cannot remove the currently active context
    - Switch to a different context first, then remove the unwanted one
    - Removed contexts cannot be recovered (you'll need to login again)

#### Purging All Contexts (`skaha auth purge`)

Remove **all** authentication contexts and credentials:

```bash
skaha auth purge
```

!!! danger "Complete Removal"
    This command permanently deletes:

    - All saved authentication contexts
    - Your entire Skaha configuration file (`~/.config/skaha/config.yaml`)
    - You'll need to login again to use Skaha

**Options:**
```bash
# Skip confirmation prompt
skaha auth purge --yes

# Interactive confirmation (default)
skaha auth purge
```

---

## Programmatic Authentication

Once you have authentication contexts set up via the CLI, you can use them programmatically in your Python code.

### Using Active Context

The simplest approach uses your currently active authentication context:

```python
from skaha.session import Session

# Uses the active authentication context automatically
session = Session()

# Check which context is being used
print(f"Active context: {session.config.active}")
print(f"Auth Context: {session.config.context}")
```

### Authentication Priority

When creating a Session, Skaha follows this priority order:

1. **User-provided token** (highest priority)
2. **User-provided certificate**
3. **Active authentication context**
4. **Default certificate location** (`~/.ssl/cadcproxy.pem`)

```python
from pathlib import Path
from pydantic import SecretStr
from skaha.session import Session

# Priority 1: Direct token (overrides everything)
session = Session(token=SecretStr("your-bearer-token"))

# Priority 2: Direct certificate (overrides context)
session = Session(certificate=Path("/path/to/cert.pem"))

# Priority 3: Uses active context (most common)
session = Session()
```

## Troubleshooting

### Common Authentication Issues

!!! question "Login Problems"

    **No servers found during discovery**

    - Check your internet connection
    - Try `skaha auth login --dead` to include non-responsive servers
    - Verify you're not behind a restrictive firewall

    **Authentication failed**

    - Verify your username and password are correct
    - Check if your account is active on the Science Platform
    - Try logging into the web interface first

    **Certificate expired**

    - X.509 certificates typically last 10 days
    - Run `skaha auth login --force` to refresh
    - Check expiry with your authentication status code above

!!! question "Context Management Issues"

    **No active context found**

    - Run `skaha auth list` to see available contexts
    - Use `skaha auth switch <context>` to activate one
    - If no contexts exist, run `skaha auth login`

    **Cannot remove active context**

    - Switch to a different context first: `skaha auth switch <other>`
    - Then remove the unwanted context: `skaha auth remove <unwanted>`

### Debug Mode

Enable detailed authentication logging:

```bash
# CLI debug mode
skaha auth login --debug
```

### Getting Help

!!! tip "Support Resources"
    - 📖 [CLI Reference](cli-help.md) - Complete command documentation
    - 💬 [Community Discussions](https://github.com/shinybrar/skaha/discussions) - Ask questions
    - 🐛 [Report Issues](bug-reports.md) - Bug reports and feature requests
```
