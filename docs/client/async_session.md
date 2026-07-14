# Asynchronous Sessions

!!! info "Overview"
    `canfar` supports asynchronous sessions using the `AsyncSession` class while maintaining 1-to-1 compatibility with the `Session` class.

## Creating sessions

`AsyncSession.create` matches `Session.create`: it returns a `list` of session
IDs, omits failed launches without raising, and returns an empty list if every
attempt fails. Check the list after awaiting the call. HTTP and timeout details
are logged when the application configures logging. Call
`canfar.configure_logging()` at the Python application entry point; it honors
`CANFAR_LOGLEVEL`. In the CLI, use a root control such as
`canfar --log-level debug create ...`. See
[Logging](../cli/logging.md).

::: canfar.sessions.AsyncSession
    handler: python
    selection:
      members:
        - fetch
        - create
        - info
        - logs
        - destroy
        - connect
    rendering:
      members_order: source
      show_root_heading: true
      show_source: true
      heading_level: 2
