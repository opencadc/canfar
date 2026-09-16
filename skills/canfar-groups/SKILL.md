---
name: canfar-groups
description: >
  CANFAR groups and teams: CADC Group Management or deployment GMS/permissions,
  member/admin roles, project allocation access, POSIX group mapping, VOSpace
  ACLs, and Container Registry roles. Use when adding a collaborator, student,
  PI, team membership, group admin, or diagnosing project access.
---
# Groups & collaboration

Groups are a foundation of team access, but membership is only one layer. A
project allocation, filesystem ownership/mode, VOSpace ACL, or registry role can
still deny access after the user joins the group.

At CADC, use [CADC Group Management](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/).
SRCNet/other deployments may expose an IVOA GMS service or Permissions API with
a different user interface. Ask the PI/project admin or follow the site's portal.

## Roles

| Role | Can do |
| --- | --- |
| **Administrator** | Add/remove members, assign admins, manage group resources |
| **Member** | Use shared resources the group grants (CADC example: `/arc/projects/…`) |

## CADC: create a research group

1. Group Management portal → **New Group**
2. Descriptive name (e.g. `cfhtls-survey`, `exoplanet-collab`)
3. Project description → **Create**

## CADC: add team members

1. **Edit** in the Membership column
2. Search by **full name** (e.g. "Jane Doe") — not always by username
3. Select user → **Add member**

## Assign administrators

1. **Edit** in the Administrators column
2. Add users who should manage membership and allocations

## Group to Session and storage access

- Skaha obtains the user's supplemental groups through the deployment's identity,
  GMS/permissions, and POSIX Mapper integration.
- A project path such as `/arc/projects/<project>/` (CADC) is a managed allocation with
  filesystem ownership and quota; group membership alone does not create it.
- New membership may take time to reach caches or may require a fresh Session.
- Creating a project allocation is **not** `mkdir` — admin/allocation workflow (see `canfar-permissions`)

## External collaborators

PI/admin adds external partners when site policy and identity federation allow.
Do not assume a CADC identity automatically grants SRCNet or another site's access.

## Troubleshooting

| Problem | Check |
| --- | --- |
| Permission denied on project path | Check identity, membership, allocation, path group/mode, then cache/new Session |
| User cannot launch any Session | Check deployment platform-access group or Permissions API entitlement |
| User can launch but cannot push images | Check Container Registry project role separately |

Related: `canfar-permissions` (ACLs), `canfar-storage` (paths)
