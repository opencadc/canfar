# Authentication Guide

CANFAR Python Client and CLI are designed to connect to multiple Science Platform servers around the world. This guide covers everything you need to know about authentication, from basic set-up to advanced scenarios.

## Authentication Overview

CANFAR clients use an **Authentication Context** system to manage connections to different Science Platform servers. This system supports multiple authentication methods and makes it easy to switch between servers.

### What is an Authentication Context?

Think of an authentication context (*context* for short) as a saved profile that contains:

- **Server information** (URL, capabilities)
- **Authentication credentials** (X.509 certificate, OIDC tokens, etc.)
- **User preferences** for that specific server

When you use CANFAR, one context is always **active**, and all commands and API calls are directed to that server.

### Authentication Methods

CANFAR supports several authentication methods:

!!! info "Authentication Methods"
    - **X.509 Certificates** - Most common, uses `.pem` certificate files
    - **OIDC Tokens** - OpenID Connect for modern authentication flows
    - **Bearer Tokens** - Direct token authentication for API access

!!! tip "Automatic Configuration"
    CANFAR automatically configures the appropriate authentication method based on the server's capabilities and your configuration.

---

## CLI Authentication Management

The CANFAR CLI provides comprehensive commands for managing your authentication contexts.


### Initial Login (`canfar login`)

The `login` command is your starting point for connecting to any Science Platform server:

```bash
canfar login
```

`canfar auth login` remains available as a deprecated compatibility alias.

**What happens during login:**

1. **IDP Selection** - Choose a built-in Identity Provider, or pass `cadc` or `srcnet` explicitly
2. **Authentication Flow** - Guides you through the selected IDP's authentication method
3. **Server Discovery** - Finds Science Platform servers scoped to the selected IDP
4. **Server Selection** - Selects or prompts for a compatible Science Platform server
5. **Activation** - Saves the active Authentication and Server Selection for immediate use

!!! example "Login Options"
    ```bash
    # Guided login
    canfar login

    # Explicit IDP login
    canfar login cadc

    # Include development servers during discovery
    canfar login --dev

    # Increase login HTTP request timeout
    canfar login --timeout 10

    # Force re-authentication for an existing IDP
    canfar login --force
    ```

### Managing Multiple Contexts

Once you have one or more authentication contexts, you can easily manage them:

#### Listing Providers (`canfar auth ls`)

View saved authentication providers:

```bash
canfar auth ls
```

**Example Output:**
```
                  Available Authentication Contexts                  
                                                                     
  Active   Name          Auth Mode   Server URL                      
 ─────────────────────────────────────────────────────────────────── 
    ✅     canfar          x509      https://ws-uv.canfar.net/skaha  
                                                                     
           SRCnet-Sweden   oidc      https://services.swesrc.chalmers.se/skaha
```

The active context (marked with ✅) determines where your commands are sent.

#### Switching Providers (`canfar auth use`)

Switch between saved authentication providers:

```bash
canfar auth use <IDP>
```

!!! example "Switching Examples"
    ```bash
    canfar auth use srcnet
    canfar auth use cadc
    ```

All subsequent commands will use the newly active context.

#### Removing Providers (`canfar auth rm`)

Remove authentication providers you no longer need:

```bash
canfar auth rm <IDP>
```

!!! warning "Safety Features"
    - You cannot remove the currently active context
    - Switch to a different context first, then remove the unwanted one
    - Removed contexts cannot be recovered (you'll need to login again)

#### Purging All Contexts (`canfar auth purge`)

Remove **all** authentication contexts and credentials:

```bash
canfar auth purge
```

!!! danger "Complete Removal"
    This command permanently deletes:

    - All saved authentication contexts
    - Your entire canfar configuration file (`~/.config/canfar/config.yaml`)
    - You'll need to login again to use canfar

**Options:**
```bash
# Skip confirmation prompt
canfar auth purge --yes

# Interactive confirmation (default)
canfar auth purge
```

---

## Programmatic Authentication

Once you have authentication contexts set up via the CLI, you can use them programmatically in your Python code.

### Using Active Context

The simplest approach uses your currently active authentication context:

```python
from canfar.session import Session

# Uses the active authentication context automatically
session = Session()

# Check which context is being used
print(f"Active context: {session.config.active}")
print(f"Auth Context: {session.config.context}")
```

### Authentication Priority

When creating a session, canfar follows this priority order:

1. **User-provided token** (highest priority)
2. **User-provided certificate**
3. **Active authentication context**
4. **Default certificate location** (`~/.ssl/cadcproxy.pem`)

```python
from pathlib import Path
from pydantic import SecretStr
from canfar.session import Session

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
    - Use `canfar login --dev` only when you need development servers
    - Increase request timeouts with `canfar login --timeout 10`
    - Verify you're not behind a restrictive firewall

    **Authentication failed**

    - Verify your username and password are correct
    - Check if your account is active on the Science Platform
    - Try logging into the web interface first

    **Certificate expired**

    - X.509 certificates typically last 10 days
    - Run `canfar login --force` to refresh
    - Check expiry with your authentication status code above

!!! question "Context Management Issues"

    **No active context found**

    - Run `canfar auth ls` to see available providers
    - Use `canfar auth use <idp>` to activate one
    - If no contexts exist, run `canfar login`

    **Cannot remove active context**

    - Switch to a different authentication first: `canfar auth use <idp>`
    - Then remove the unwanted provider: `canfar auth rm <IDP>`

### Debug Mode

Enable detailed authentication logging:

```bash
# CLI debug mode
canfar login --debug
```
