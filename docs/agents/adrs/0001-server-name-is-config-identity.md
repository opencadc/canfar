# Server Name is the configuration identity for Science Platform Servers

Client configuration stores Science Platform Servers as `servers: Dict[str, Server]` keyed by Server Name, and Authentication Records as `authentication: Dict[str, AuthenticationCredential]` keyed by IDP. Server Selection (`active.server`) and remembered selections (`active.servers`) reference Servers by name, not IVOA URI. We chose name over URI because dotted-path config access (`canfar config get servers.canfar.url`) needs keys without dots, and users think in names. Schema stays v1: v1 has not shipped, so no migration is required.

## Consequences

- The IVOA URI is discovery metadata only. Discovery upserts match by name; the same URI may legitimately appear under two names, and registry renames create a new entry rather than rewriting the user's key.
- Server Names must match `^[A-Za-z][A-Za-z0-9_-]*$` so they are safe as dotted-path segments (no dots, never digits-only) and env-var segments (`CANFAR_SERVERS__<name>__URL`).
- Servers discovered without a registry name are keyed by a slug of the URI host (e.g. `ivo://swesrc.chalmers.se/skaha` -> `swesrc-chalmers-se`). Two unnamed servers on one host collide; the registry must name them to disambiguate.
- `Server.name` and `AuthenticationCredential.idp` remain on the Python models for display and selection but are excluded from serialization; `Configuration` injects the dict key into each value on load.

## Considered options

- `Dict[str, Server]` keyed by IVOA URI: rejected, URIs contain dots and slashes and are hostile to dotted paths and env vars.
- Keep `list[Server]` and teach the dotted-path editor name-based selectors: rejected, dict gives native path access with no editor magic, and pre-ship there is no migration cost.
- Match discovery upserts by URI instead of name: rejected to keep name as the single identity; duplicate URIs under two names are acceptable.
