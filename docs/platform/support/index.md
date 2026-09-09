# Support

Start with the guide for the component that failed, then contact the service
operator with a small, reproducible diagnostic set.

## Check the documentation first

- [Getting started](../get-started.md) covers login, server selection, and a
  first Session.
- [Storage](../storage/index.md) covers Storage Identifiers, `/arc`,
  `/scratch`, and Python filesystems.
- [Batch processing](../sessions/batch.md) explains `Pending`, queueing,
  creation output, and headless troubleshooting.
- [Permissions](../permissions.md) explains identity, project groups, images,
  and access-denied errors.
- [FAQ](faq.md) collects short answers and command examples.

## Fast checks

### Login or server selection

```bash
canfar login cadc
canfar server ls
canfar server use SERVER_NAME
canfar config get active.server -o json
```

Use the Identity Provider (IDP) and Server Name supplied by your platform operator.
Do not paste certificates, tokens, or passwords into a support request.

### A Session is not ready

`Pending` means the platform accepted the request but has not made the Session
ready. It can include admission, resource, image-pull, or initialization work.
Inspect the Session and its events before changing the request:

```bash
canfar ps --all
canfar info SESSION_ID
canfar events SESSION_ID
canfar stats
```

`canfar logs SESSION_ID` is useful after the container has started. A Pending
Session may not have application logs yet. See [batch troubleshooting](../sessions/batch.md#monitor-and-troubleshoot).

### A data operation fails

Confirm the identifier and path, then check group membership with the project
administrator:

```bash
canfar data ls -lh IDENTIFIER:/path
canfar data info IDENTIFIER:/path/to/file
canfar data stat IDENTIFIER:/path/to/file
```

Use `/scratch` for temporary staged data and `/arc` or a persistent VOSpace
Service for outputs that must survive a Session. See [data transfers](../storage/transfers.md).

### A browser Session does not open

Confirm that the Session is ready with `canfar ps --all` and `canfar info
SESSION_ID`. Then retry the link in a current browser or private window. If
the Session is Running but the endpoint remains unreachable, report the
Session ID, Server Name, timestamp, and browser error to support.

## Contact CANFAR support

Email [support@canfar.net](mailto:support@canfar.net) for account access,
project membership, persistent data errors, service outages, or a Session that
remains Pending after the platform's normal queue interval. Include:

- the Server Name and Identity Provider (IDP);
- the command or UI action, with paths and image references redacted as needed;
- the Session ID and status, if applicable;
- the time and timezone;
- exact error text; and
- relevant `info`, `events`, or `stats` output.

Send security vulnerabilities privately; see the [security policy](../../security.md).
Do not include passwords, tokens, certificates, or private data in email or
public issues.

## Community and bug reports

Use the [CANFAR Discord](https://discord.gg/vcCQ8QBvBa) for community
questions and the [GitHub issue tracker](https://github.com/opencadc/canfar/issues)
for reproducible bugs or documentation changes. Search existing issues first
and include a minimal reproduction.
