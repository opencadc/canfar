# Session API

!!! info "Overview"
    The `Session` API is the core of canfar, enabling you to create, manage, and destroy sessions on the CANFAR Science Platform.

## Creating sessions

`Session.create` returns a `list` of session IDs (strings) for each successful launch. If the platform rejects a request or
the call hits a network or HTTP error, that launch is skipped and logging records the failure. If every launch fails, you get an
empty list. The method does not raise for those errors, so callers can check `if not ids:` (or compare the length to `replicas`)
after the call. For details in Python, call `canfar.configure_logging()` at the
application entry point; it honors `CANFAR_LOGLEVEL`. In the CLI, use a root
control such as `canfar --log-level debug create ...`. See
[Logging and observability](../cli/logging.md).

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
