# Server Name is the configuration identity for Science Platform Servers

Client configuration stores Science Platform Servers as `servers: Dict[str, Server]` keyed by Server Name, and Authentication Records as `authentication: Dict[str, AuthenticationCredential]` keyed by IDP. Server Selection (`active.server`) and remembered selections (`active.servers`) reference Servers by name, not IVOA URI. We chose name over URI because dotted-path config access (`canfar config get servers.canfar.url`) needs keys without dots, and users think in names. The written schema is version 2. A version 1 file is deep-merged onto the current defaults and rewritten as version 2 the first time it loads.

## Consequences

- The IVOA URI is discovery metadata only. Discovery upserts match by name; the same URI may legitimately appear under two names, and registry renames create a new entry rather than rewriting the user's key.
- Server Names must match `^[A-Za-z][A-Za-z0-9_-]*$` so they are safe as dotted-path segments (no dots, never digits-only) and env-var segments (`CANFAR_SERVERS__<name>__URL`).
- Servers discovered without a registry name are keyed by a slug of the URI host (e.g. `ivo://swesrc.chalmers.se/skaha` -> `swesrc-chalmers-se`). Two unnamed servers on one host collide; the registry must name them to disambiguate.
- `Server.name` and `AuthenticationCredential.idp` remain on the Python models for display and selection. They are duplicated in saved YAML alongside dict keys; dict keys remain canonical on load (inject overwrites missing or drifted values).

## Considered options

- `Dict[str, Server]` keyed by IVOA URI: rejected, URIs contain dots and slashes and are hostile to dotted paths and env vars.
- Keep `list[Server]` and teach the dotted-path editor name-based selectors: rejected, dict gives native path access with no editor magic. v1 had not shipped when this was chosen.
- Match discovery upserts by URI instead of name: rejected to keep name as the single identity; duplicate URIs under two names are acceptable.
