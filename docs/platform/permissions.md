# Accounts, groups, and permissions

Your Canadian Astronomy Data Centre (CADC) account identifies you to CANFAR.
A group lets a project share access with several accounts. Signing in confirms
who you are; access to a directory or private image depends on the permissions
its owner grants you.

## Create a project group

You need a CADC account to create a group. If your project already has one,
ask one of its administrators to add you instead.

1. Sign in to [CADC Group Management](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/).
2. Select **New Group** and enter a descriptive **Name** and **Description**.
3. Select **Create** and find the new group in the list.

Creating a group does not allocate project storage, set a quota, or create a
container registry project. Contact [CANFAR support](support/index.md) to
request a shared storage allocation and provide your group name.

## Add members and administrators

You must be an administrator of the group to change its membership.

1. Open the group's membership editor and find the **Members** section.
2. Search for your colleague by name, check the account in the results, and
   select **Add member**.
3. To let a colleague manage membership too, use **Add administrator** in the
   **Administrators** section.
4. Select **Update** to save changes. Reopen the group and confirm that the
   intended accounts appear in the member or administrator list.

Administrator status allows group management. It does not grant authority to
allocate platform resources or edit data owned by someone else.

## Grant the group access to data

The directory owner or a person allowed to change its permissions must grant
access separately from adding group members.

1. Open [Storage Management](https://www.canfar.net/storage/arc/list) and
   navigate to the directory you want to share.
2. Open its permissions editor and assign your group to **Read** for access
   without edits, or **Read/Write** if collaborators need to change the data.
3. Save the change. Check the permissions on the files and subdirectories you
   intend to share; do not assume that changing one directory updates every
   existing child.
4. Ask a group member to sign in with their own account and open a sample
   file. For write access, have them create and remove a small test file in
   the agreed directory.

If you cannot edit permissions, ask the directory owner or CANFAR support.
Use the path supplied for your allocation rather than assuming it matches the
group name.

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
operator for that Science Platform deployment. See the [authentication guide](../cli/authentication-contexts.md) for credential and server selection details.

## Check access from the command line

For data operations, start by listing the identifiers and paths you can use:

```bash
canfar data ls -lh arc:/projects/PROJECT
canfar data info arc:/projects/PROJECT/catalog.csv
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
credential as described in the [HTTP client guide](../client/client.md) and
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
