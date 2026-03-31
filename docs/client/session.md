# Session API

!!! info "Overview"
    The `Session` API is the core of canfar, enabling you to create, manage, and destroy sessions on the CANFAR Science Platform.

## Creating sessions

`Session.create` returns a `list` of session IDs (strings) for each successful launch. If the platform rejects a request or
the call hits a network or HTTP error, that launch is skipped and logging records the failure. If every launch fails, you get an
empty list. The method does not raise for those errors, so callers can check `if not ids:` (or compare the length to `replicas`)
after the call. For details, enable library logging (for example set `CANFAR_LOGLEVEL=DEBUG` or use the CLI `--debug` flag on commands
that support it).

::: canfar.sessions.Session
    handler: python
    selection:
      members:
        - fetch
        - create
        - info
        - logs
        - destroy
    rendering:
      members_order: source
      show_root_heading: true
      show_source: true
      heading_level: 2
