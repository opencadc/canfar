---
name: canfar
description: Operate the CANFAR Science Platform with the `canfar` CLI and Python client - launch and inspect Sessions (notebook, desktop, CARTA, Firefly, contributed, headless), scale out replicated batch jobs, move data through Storage Identifiers, script workflows in Python, and answer platform questions from the CANFAR docs. Use for any work on CANFAR, CADC, or SRCNet compute.
---

# Work on the CANFAR Science Platform

Carry out the user's request with their installed `canfar` client. A
**Session** is a user-owned compute environment on a **Science Platform
Server**, started from a **Container Image**. Its **Session Kind** is
`notebook`, `desktop`, `carta`, `firefly`, `contributed`, or `headless`.

Three states mark progress. Claim only the one you observed:

- **accepted**: `create` returned a Session ID.
- **Running**: the Session reports `status` `Running` and a nonempty `connectURL`.
- **verified**: the expected output exists on persistent storage and passed its check.

## Start every task here

1. **Route the request.**

   | The request is about | Read |
   | --- | --- |
   | Launching, opening, inspecting, or deleting a Session | [Launch a Session](#launch-a-session) below |
   | Headless commands, replicas, pipelines, many Sessions | [references/batch.md](references/batch.md) |
   | A Python script or notebook that drives CANFAR | [references/python.md](references/python.md) |
   | Listing, copying, or reading files on `arc`, `vault`, or another Storage Identifier | [references/data.md](references/data.md) |
   | How the platform works: storage, images, permissions, DOI, CVMFS, support | [Platform questions](#platform-questions) below |

   A platform question needs only its page. Every other branch runs steps 2
   and 3, then reads its reference before composing commands.
2. **Installed interface.** Run `canfar version` and `canfar ps --help`. This
   skill matches the installed client when that help lists `-o, --output`; the
   version number alone does not tell, because a development checkout can
   carry an older one. Without `-o`, the client predates this skill: say so,
   and compose every command from its own `--help`. With it, read a command's
   `--help` before adding a flag this skill does not show; that help is the
   authority for flags. Work in the user's existing environment, and install
   only on request with its package manager (`uv add canfar`, or
   `pip install canfar` in a virtual environment).
3. **Identity and Server.** `canfar auth show -o json` prints the active
   Authentication Record and `canfar server ls -o json` the Servers. The
   identity is usable when `canfar ps -o json` exits 0; keep its payload, the
   user's active Sessions. An `expiry` of `null`, or an `authentication.*`
   error code on stderr, means login is needed: **hand login to the user**.
   Ask them to run `canfar login IDP` in their own terminal, with the record's
   `idp` (`cadc` for a CADC certificate, `srcnet` for the SRCNet OpenID Connect
   device flow), because credential entry and browser approval are theirs.
   Tell them what you will do once they are back, and resume when
   `canfar ps -o json` exits 0. With several Servers, confirm the target before
   submitting work; `canfar server use SELECTOR` takes a Server Name or IVOA
   URI.
4. **Report.** Finish with the Session IDs, the state you observed for each
   (accepted or Running, and verified for work that writes outputs), any paths
   you verified, and the command that cleans up this work.

## Launch a Session

1. **Reuse.** When the active Sessions from `canfar ps -o json` already hold
   one of the requested Kind, offer its `connectURL` before launching another;
   a Server limits how many interactive Sessions one user runs.
2. **Image.** Use the image the user named. Otherwise list the Kind's images
   with `canfar image ls --kind notebook` and choose from that listing:
   `skaha/astroml` is the general-purpose astronomy image the CANFAR docs use,
   so pick it when listed and say so. The listing is the source of truth for
   names and Kinds on the chosen Server; pin a version tag when the work must
   be repeatable. The client adds `images.canfar.net/` and `:latest` to a short
   name such as `skaha/astroml`.
3. **Create.** Name the Session for the work; without `--name` the client
   generates one. Pass `--cpu` and `--memory` (GB) together only when the user
   gives sizes or a test run measured them; without them the Server applies
   its flexible policy, and fixed requests can wait longer for capacity.
   `--gpu N` requests GPUs.

   ```bash
   canfar create notebook IMAGE --name analysis -o json
   ```

   Stdout is a JSON array of Session IDs, such as `["a1b2c3d4"]`. Done when
   you hold that ID: the Session is **accepted**. On a failure, read the
   `hint` in the error and check `canfar ps --all -o json` before retrying,
   because a request whose response was lost can still have been accepted.
   When the Server refuses the launch for a Session limit, show the user their
   Sessions and let them choose what to delete. `--dry-run`, used without
   `-o`, parses a request locally and exits; it checks the arguments, not the
   image, the login, or capacity.
4. **Wait for Running.** Poll `canfar ps --all -o json` every 10 seconds for up
   to 5 minutes. It prints a JSON array of Session objects with `id`, `name`,
   `type`, `image`, `status`, `connectURL`, `startTime`, and `expiryTime`;
   find yours by `id`. `--all` matters: without it a Session that fails leaves
   the listing instead of showing `Failed`. Done when `status` is `Running`
   and `connectURL` is nonempty. After a minute of `Pending`, run
   `canfar events SESSION_ID` once and tell the user whether it waits on
   admission, resources, or an image pull. When the budget ends, or the status
   turns `Failed` or `Error`, report `canfar events SESSION_ID` and
   `canfar logs SESSION_ID`, and keep the one Session you launched.
5. **Hand over.** Give the user the `connectURL`, the Session ID, and its
   `expiryTime`. On the user's own machine, `canfar open SESSION_ID` opens it
   in their browser; on a remote machine, print the URL. The Session stays up
   until the user asks for deletion. Remind them that work saved outside
   `/arc` ends with the Session.

```bash
canfar ps --all -o json
canfar info SESSION_ID
canfar events SESSION_ID
canfar logs SESSION_ID
canfar open SESSION_ID
canfar delete SESSION_ID
```

`ps` shows Pending and Running Sessions; add `--all` to see terminal ones,
including with `--status`. `desktop` and `firefly` Sessions take one replica
and the Server's own resource sizes. `cmd`, `args`, and `--env` belong to
`headless` Sessions.

## Where data lives

These are the CADC deployment's names; on another Server, discover the mounts
and Storage Identifiers it provides.

| Location | Lifetime | Use it for |
| --- | --- | --- |
| `/arc/home/USER` | Persistent | Personal scripts, configuration, results |
| `/arc/projects/PROJECT` | Persistent | Project data and shared results |
| `/scratch` | Deleted with the Session | Staging and intermediate files |
| `arc:`, `vault:` Storage Identifiers | Service-defined | Remote access from any machine through `canfar data` or Python |

Save every result the user needs under persistent storage before a Session
ends. A path on the user's laptop exists inside a Session only after it is
copied to storage that Session mounts, or built into the image.

## Output and cleanup

- **Machine output** (`-o json` or `-o yaml`, placed on the owning command): `auth`, `auth show`, `auth ls`, `server ls`, `create`, `ps`, `config show`, `config get`.
- **Human text only**: `info`, `logs`, `events`, `open`, `delete`, `prune`, `stats`, `image ls`, `version`.

With `-o`, stdout carries only the payload, and a failure exits nonzero with
`code`, `message`, and `hint` as JSON on stderr. Select list items by ID or
name rather than by position. Human-text commands print an `@SERVER` banner
first and report problems in plain text. Releases up to 1.4.1 exit 0 on an
authentication failure, so judge those commands by what they print:
`canfar image ls` showing no image rows beside an authentication message
means login, not an empty registry. Root logging options go before the
command, as in `canfar --log-level debug ps -o json`; debug logs can include
response bodies, so keep them out of shared reports. `--log-file PATH` adds a
rotating JSON Lines log.

Cleanup scope is the Session IDs this work created, deleted only when the user
asks: `canfar delete SESSION_ID`, adding `--force` to skip the confirmation
once the user has authorized that deletion.

## Platform questions

Answer from the page, then cite it. Fetch the URL, or in a checkout of
`opencadc/canfar` read the same path under `docs/` (`.../platform/doi/` is
`docs/platform/doi.md`).

Answer for the person asking: lead with the Science Portal
(https://www.canfar.net/) route for someone working in a browser, and with the
CLI or Python for someone automating. Live output from the user's Server
(`canfar info SESSION_ID`, `canfar image ls`, `df -h` inside a Session)
outranks a documented default, which describes the CADC deployment.
Irreversible platform actions, such as publishing a DOI or making data public,
wait for the user's explicit instruction.

| Topic | Page |
| --- | --- |
| Accounts, access, first steps | https://www.opencadc.org/canfar/latest/platform/get-started/ |
| Concepts and architecture | https://www.opencadc.org/canfar/latest/platform/concepts/ |
| Session Kinds and lifecycle | https://www.opencadc.org/canfar/latest/platform/sessions/ |
| Notebook, Desktop, CARTA, Firefly, Contributed | https://www.opencadc.org/canfar/latest/platform/sessions/notebook/ and its sibling pages `desktop/`, `carta/`, `firefly/`, `contributed/` |
| Batch queueing and Pending diagnosis | https://www.opencadc.org/canfar/latest/platform/sessions/batch/ |
| Session limits, lifetime, out-of-memory, what a Session was granted | https://www.opencadc.org/canfar/latest/platform/sessions/limits/ |
| Storage, quotas, requesting space | https://www.opencadc.org/canfar/latest/platform/storage/ |
| Filesystem access, remote reads, caching | https://www.opencadc.org/canfar/latest/platform/storage/filesystem/ |
| Transfers | https://www.opencadc.org/canfar/latest/platform/storage/transfers/ |
| VOSpace, sharing, legacy `vos` tools | https://www.opencadc.org/canfar/latest/platform/storage/vospace/ |
| Groups, permissions, access denied | https://www.opencadc.org/canfar/latest/platform/permissions/ |
| Container Images, building, the registry | https://www.opencadc.org/canfar/latest/platform/containers/ and `build/`, `registry/` |
| Pipeline design and resource sizing | https://www.opencadc.org/canfar/latest/platform/best-practices/ |
| CVMFS software stacks | https://www.opencadc.org/canfar/latest/platform/cvmfs/ |
| Publishing data with a DOI | https://www.opencadc.org/canfar/latest/platform/doi/ |
| FAQ, support, reporting a problem | https://www.opencadc.org/canfar/latest/platform/support/faq/ and https://www.opencadc.org/canfar/latest/platform/support/ |
| Authentication Records and Server Selection | https://www.opencadc.org/canfar/latest/cli/authentication-contexts/ |
| CLI reference, logging | https://www.opencadc.org/canfar/latest/cli/cli-help/ and https://www.opencadc.org/canfar/latest/cli/logging/ |
| Acknowledging CANFAR in a paper | https://www.opencadc.org/canfar/latest/about/acknowledgement/ |
