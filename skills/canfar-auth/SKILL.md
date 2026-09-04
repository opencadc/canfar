---
name: canfar-auth
description: >
  CANFAR Authentication and Science Platform Server Selection: canfar login,
  CADC X.509, SRCNet OIDC, IVOA registry discovery, auth/server inspection,
  proxy certificates, and automation. Use when login fails or the user asks
  about identity, credentials, IDPs, SRCNet, or choosing a Server.
---
# Authentication and Server Selection

CANFAR separates **who you are** (Authentication) from **where new requests go**
(Server Selection).

Docs: [Authentication and Servers](https://www.opencadc.org/canfar/latest/cli/authentication-contexts/)

## Built-in Identity Providers

| IDP | Authentication mode | Preferred primary VOSpace registry leaf |
| --- | --- | --- |
| `cadc` | X.509 proxy certificate | `arc` (plus CADC `vault`) |
| `srcnet` | OIDC through SKA IAM | `cavern` |

`canfar login` authenticates, discovers compatible Science Platform Servers
through an IVOA Registry, selects one, and saves the active pair. Existing
Sessions stay on the Server where they were launched when selection changes.

## Interactive login

```bash
canfar login              # choose IDP and Server
canfar login cadc
canfar login srcnet
canfar login cadc --force
canfar --log-level debug login cadc --force
```

## Inspect, switch, or remove

```bash
canfar auth show
canfar auth ls
canfar auth use srcnet
canfar server ls
canfar server use <server-name-or-ivoa-uri>
canfar auth rm cadc
canfar auth purge --force
```

There is no `canfar logout`. `auth rm` removes one Authentication record and its
Servers; `auth purge` resets all Authentication/Server state while preserving
unrelated configuration.

Configuration is stored at `~/.canfar/config.yaml`. It persists across Sessions
only when the site mounts a persistent home at that location (CADC does).

## Proxy certificates and legacy tools

```bash
cadc-get-cert -u $USER
```

The current `cadc-get-cert` default is 10 days and writes
`~/.ssl/cadcproxy.pem`. Prefer `canfar login` for new workflows; renew an expired
certificate rather than embedding credentials.

## Automation

Run interactive login on the machine/filesystem the job will use, or construct
the Python client with an explicit runtime token/certificate. Prefer a Server URI
in scripts; human-readable Server Names can differ by deployment.

## Agent rules

1. Check `canfar auth show` and `canfar server ls` before blaming a Session API.
2. Never ask users to paste passwords, tokens, or certificates into scripts/chat.
3. `canfar auth login` is a deprecated compatibility alias; use `canfar login`.
4. A valid identity can still lack platform entitlement, group membership, or data access.
