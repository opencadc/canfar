# Accounts, groups, and permissions

CANFAR access is evaluated at several boundaries: your CADC identity, the
active Science Platform Server, the Storage Identifier you use, the project
groups that grant access, and the Container Image you request. A successful
login does not grant access to every server, project, image, or data object.

## Identity and server access

Authenticate with the Identity Provider (IDP) that owns the target Science Platform Server:

```bash
canfar login cadc
canfar server ls
canfar server use SERVER_NAME
canfar config get active.server
```

The names and capabilities in `canfar server ls` are deployment data. If the
server is missing or login succeeds but a request is forbidden, contact the
operator for that Science Platform deployment. See the [client
overview](../client/overview.md) for credential and server selection details.

## Groups and project data

Project storage is intended for collaboration. A project administrator grants
membership through the [CADC group management portal](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/);
the resulting permissions are enforced by the storage service. Use the paths
and Storage Identifiers supplied by your project rather than assuming that a
project name, quota, or sharing policy is the same on every deployment.

For data operations, start by listing the identifiers and paths you can use:

```bash
canfar data ls -lh arc:/projects/<project>
canfar data info arc:/projects/<project>/catalog.csv
```

`local:` refers to the machine running the command. `arc:` and `vault:` are
examples of configured remote identifiers; use the identifiers returned by
your platform configuration and the [storage guide](storage/index.md) for your
deployment. A forbidden
operation usually means that your account is not a member of the owning group,
the path is outside the project's allocation, or the active credentials do not
match the service.

Do not put credentials in a path, a notebook, an image, or a Session command.
Use the configured Authentication Record or an explicitly supplied runtime
credential as described in the [client overview](../client/overview.md) and
[storage guide](storage/index.md).

## Container images

Image visibility and push rights are controlled by the registry project. Find
images visible to the active server with:

```bash
canfar image ls
canfar image ls --kind headless
```

Use the complete reference returned by the listing. A pull failure can mean a
missing tag, a private project, or a registry that the target server cannot
reach; ask the registry or platform operator which case applies. See
[Container Registry](containers/registry.md).

## Session resources

Resource requests are checked when a Session is admitted. They do not change
data permissions or project membership. For a rejected or long-running
request, inspect the Session and its events:

```bash
canfar ps --all
canfar info SESSION_ID
canfar events SESSION_ID
```

See [batch troubleshooting](sessions/batch.md#monitor-and-troubleshoot) for
`Pending` and image-pull checks.

## When access is denied

Collect the smallest useful diagnostic set without exposing credentials:

1. the active Server Name and Storage Identifier;
2. the command shape and redacted path or image reference;
3. the Session ID and status, if a Session is involved; and
4. the exact error and relevant `info`/`events` output.

Ask the project administrator to confirm group membership and path ownership.
If membership is correct, contact the service operator through
[support](support/index.md). Do not retry destructive operations while the
ownership or path is uncertain.

## Related guides

- [Getting started](get-started.md)
- [Storage](storage/index.md)
- [Container Registry](containers/registry.md)
- [Support](support/index.md)
