# Knowledge held only by the 22 platform skills

- **Date:** 2026-09-18
- **Repository snapshot:** `feat/skills`, branched from `d77fe424` on `main`
- **Source audited:** the 22 `skills/canfar-*` skills from
  [#309](https://github.com/opencadc/canfar/pull/309), commit `4b5341d6`
  (Sébastien Fabbro). Recover any of them with
  `git show 4b5341d6:skills/canfar-limits/SKILL.md`.
- **Upstream checked:** `opencadc/science-platform` Helm values and launch
  templates, `PostAction.java`, `SessionDAO.java`
- **Question:** When the 22 skills collapse into `skills/canfar`, which points
  at `docs/`, what knowledge would be lost because `docs/` does not hold it?

## Result

21 of the 22 skills hold facts `docs/` lacks, about 100 items. This branch
upstreamed the two densest groups and corrected the contradictions that the
code settles. The rest is listed here with a proposed home, because it is
platform-operator knowledge that this repository cannot verify.

### Upstreamed on this branch

| Knowledge | Now in |
| --- | --- |
| Client request bounds, replica naming, `REPLICA_ID` / `REPLICA_COUNT` | `docs/platform/sessions/limits.md` |
| Server defaults: 4-day interactive lifetime, 14-day headless deadline, 1-hour finished-record retention, 5 active interactive Sessions, 20 to 200 GiB Session-local storage | `docs/platform/sessions/limits.md` |
| Per-user limit counts Pending and Running; headless and desktop-app are exempt; the rejection message | `docs/platform/sessions/limits.md` |
| In-Session inspection (`nproc`, `free`, cgroup `memory.max`, `df`, `nvidia-smi`) and the OOM / disk / quota symptom table | `docs/platform/sessions/limits.md` |
| Shared home and project storage across Sessions, atomic writes, SQLite and lock-heavy state, per-writer outputs | `docs/platform/storage/index.md` |
| `canfar auth login` was removed in `0e5e6470`, not kept as an alias | `docs/client/migration.md`, `docs/client/updates.md`, `AGENTS.md` |

### Contradictions the code settles

The skills named `canfar ps --json`, `canfar auth show --json`, `canfar run`,
`canfar launch`, `canfar logout`, `canfar storage`, and a `canfar auth login`
alias. None exists. `tests/test_skills.py` now rejects any such command in the
skill or the user docs.

## Decisions for maintainers

1. **Contributed application contract.** The skills say a contributed image
   must serve on port 5000 from its own `ENTRYPOINT`, and that
   `/skaha/startup.sh` applies only to desktop-apps.
   `launch-contributed.yaml` agrees: probes and `containerPort` are 5000 and
   there is no `command`. `docs/platform/sessions/contributed.md` says "Do not
   assume a fixed port or startup path". The docs look wrong or over-hedged.
2. **Is `df` a quota reading on `/arc`?** The skills use `df -h` for
   allocation; `docs/platform/storage/index.md` says `df` reports filesystem
   capacity, not a quota. A quota-aware CephFS mount would favour the skills.
3. **Is SSHFS still supported at CADC?** The storage and transfers skills
   document it; the docs retired it in `8bb5991e`.
4. **DOI reviewer access.** The skill routes it through CADC support;
   `docs/platform/doi.md` through the DPS workflow.
5. **Group administrators.** The groups skill says administrators manage
   allocations; `docs/platform/permissions.md` says they do not.

## Still to upstream

Each line is knowledge `docs/` lacks, with its proposed home. Translate
"Skaha", "Harbor", and bare "context" to the `CONTEXT.md` vocabulary.

### New page: `docs/platform/storage/archives.md` (CADC archive data)

- Archive identifiers are not VOSpace paths; discover, save to project
  storage, stage in scratch, persist results.
- `cadcget` with a `COLLECTION/file` or `cadc:` identifier, `cadc-get-cert`
  for proprietary products, `cadctap` for queries, and
  `cadcdata.StorageInventoryClient`. Verify the syntax against
  `opencadc/cadctools` first.

### `docs/platform/concepts.md` (new "Platform components" section)

- Component roles: Portal, Server, Container Registry, IVOA Registry, group
  and permissions services, POSIX Mapper, Cavern/ARC, Vault; the request flow.
- The open-source chart mounts persistent storage at `/cavern`; CADC deploys
  it as ARC at `/arc`. Cavern is the implementation, ARC the deployment name.
- The repository ownership map belongs in `docs/agents/architecture.md`.

### `docs/cli/authentication-contexts.md`

- Preferred storage per Identity Provider: `cadc` maps to `arc` plus `vault`,
  `srcnet` to `cavern` (`canfar/idp.py`).
- Configuration persists across Sessions only where the deployment mounts a
  persistent home.
- The CADC certificate from `canfar login` lasts 30 days
  (`canfar/auth/x509.py`). Run login on the filesystem the job will use.

### `docs/platform/permissions.md`

- The access chain: Authentication, platform entitlement, group membership,
  project allocation, POSIX mode or VOSpace ACL, registry role.
- POSIX recipes: `id`, `ls -ld`, `namei -l`, `chmod 664` / `755`, `chgrp`.
- VOSpace ACLs are service metadata, distinct from POSIX modes; public release
  is an explicit other-read on Vault.
- Group search matches full names; new membership can need a fresh Session.
- Headless Sessions run with the submitting user's identity.

### `docs/platform/containers/` and `sessions/contributed.md`

- An image must come from a registry host the Server allows, carry the label
  that makes it visible for a Session Kind, and run as the user's mapped UID.
- Two-part image names expand to the CADC registry, a CADC convenience.
- Contributed examples (marimo, VS Code); the optional `library` CLI from
  `opencadc/canfar-library`.

### `docs/platform/storage/`

- `vospace.md`: a Vault / ARC / scratch comparison; a "Legacy vostools"
  section (`vls`, `vcp`, `vsync`, `vmkdir`, `vchmod` with its required group
  argument, `cadc-get-cert`); `vos:` means Vault while ARC is `arc:`.
- `transfers.md`: choose by retryability and file count rather than size;
  `canfar data cp` verifies destination size; a recursive copy is not atomic;
  the direct HTTPS `curl --upload-file` route to `ws-uv.canfar.net/arc/files`.
- `index.md`: keep home for configuration and small scripts; usage can lag
  after large writes on Ceph; saves and logins fail near a full home; a
  suggested project layout.

### Smaller items

- `cvmfs.md`: `/cvmfs` looks empty until a known path is accessed; a container
  versus modules versus project-environment decision table.
- `doi.md`: checksums in the package and a pre-publish re-check; corrections
  can need a new record.
- `get-started.md` and the FAQ: who is eligible, Alliance allocations for
  larger needs, what to send in an access request.
- `best-practices.md`: `jupyter nbconvert --to script`, `MKL_NUM_THREADS`.
- `support/index.md`: users have no root in a Session; a slow Vault transfer
  through the browser wants the CLI.
- `client/session.md`: a GPU example showing `gpu=` (the request field is
  `gpus`, the CLI flag `--gpu`).

## Guidance kept in the skill

Evidence order, answering for the audience in front of you, and "never publish
a DOI without explicit authorization" are agent decision rules. They belong in
`skills/canfar`, not in the user docs.
