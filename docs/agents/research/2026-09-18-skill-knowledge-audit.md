# Knowledge held only by the 22 platform skills

- **Date:** 2026-09-18
- **Repository snapshot:** `feat/skills`, branched from `d77fe424` on `main`
- **Source audited:** the 22 `skills/canfar-*` skills from
  [#309](https://github.com/opencadc/canfar/pull/309), commit `4b5341d6`
  (Sébastien Fabbro). Recover any of them with
  `git show 4b5341d6:skills/canfar-limits/SKILL.md`.
- **Question:** When the 22 skills collapse into `skills/canfar`, which points
  at `docs/`, what knowledge would be lost because `docs/` does not hold it,
  and is that knowledge true?

## Method

An audit listed about 100 facts present in the skills and absent from `docs/`.
Each was then checked against a primary source before it entered the docs:

| Source | Used for | Pinned at |
| --- | --- | --- |
| This repository | Client bounds, error codes, Identity Provider storage, certificate lifetime | `feat/skills` |
| `opencadc/science-platform` | Launch templates, Helm values, the Session service (skaha) | `8dbf9b0b`, 2026-09-01 |
| `opencadc/deployments` | Cavern, POSIX mapper, and `sshd` charts | `4e4e614a`, 2026-09-18 |
| `opencadc/vos`, `ac`, `storage-inventory`, `reg`, `storage-ui`, `science-portal`, `canfar-portal` | Component roles | default branches, 2026-09 |
| `vos` 3.7, `cadcdata` 2.5.2, `cadctap` 0.10.1, `cadcutils` 1.6.2 from PyPI | Legacy command syntax, from `--help` and source only | installed 2026-09-18 |
| `fsspec-cli` 0.7.0 as pinned by this project | `canfar data cp` verification | installed 2026-09-18 |

No service was contacted and no credential was used.

## Verified and upstreamed

| Knowledge | Now in |
| --- | --- |
| Client request bounds, Session name characters, replica naming, `REPLICA_ID` / `REPLICA_COUNT` | `platform/sessions/limits.md` |
| Flexible defaults (1 core / 4 GB bursting to 8 / 32), fixed requests, fixed `desktop` and `firefly` sizes | `platform/sessions/limits.md` |
| 4-day interactive lifetime, 14-day headless deadline with no restart, finished-record retention (1 hour headless, 1 day interactive), Session renewal in the Server API | `platform/sessions/limits.md` |
| Per-user limit of 5: counts Pending and Running, exempts headless and desktop-app, exact rejection message | `platform/sessions/limits.md`, `platform/support/index.md` |
| Session-local storage 20 GiB to 200 GiB (2 to 10 GiB for `desktop`); `/scratch` is an `emptyDir` that survives a container restart | `platform/sessions/limits.md` |
| The Server sets `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `JULIA_NUM_THREADS` to the requested cores, so `1` in a flexible Session | `limits.md`, `best-practices.md`, `containers/index.md`, the skill |
| In-Session inspection and the out-of-memory, disk, and quota symptom table | `platform/sessions/limits.md` |
| Contributed contract: TCP 5000 probes and port, image entrypoint runs, non-root with capabilities dropped, `/bin/sh` and `cp` required, URL prefix `/session/contrib/ID/` stripped before the container | `platform/sessions/contributed.md` |
| Trusted registry hosts; registry labels drive listing only, refreshed every 30 minutes; a Dockerfile `LABEL` is ignored; unlisted or private images need registry credentials; per-Kind image expectations | `platform/containers/index.md`, `registry.md` |
| Server error messages for the Session limit, untrusted registry, and private image; no root in a Session | `platform/support/index.md` |
| The access chain; memberships are read when a Session starts; headless runs as the user; `id`, `ls -ld`, `namei -l` | `platform/permissions.md` |
| Platform components and the Session creation sequence; Cavern at `/cavern` upstream, ARC at `/arc` on CADC | `platform/concepts.md` |
| Repository map for contributors | `agents/architecture.md` |
| `canfar login cadc` writes `~/.ssl/cadcproxy.pem` for 30 days; legacy tools read the same file; CADC injects a delegated certificate into each Session; no logout command | `cli/authentication-contexts.md` |
| Two-part image names always expand to `images.canfar.net`; replicas 1 to 512 | `cli/cli-help.md` |
| `gpu=` in Python against `gpus` in the request model | `client/session.md` |
| `canfar data cp` checks destination size; a recursive copy is not a snapshot | `platform/storage/transfers.md` |
| Shared home and project storage across Sessions, atomic writes, lock-heavy state on scratch | `platform/storage/index.md` |
| CVMFS is an operator-side mount, absent from the open-source chart; where software should live | `platform/cvmfs.md` |
| Legacy vostools: schemes, `vls`, `vcp`, `vsync`, `vmkdir -p`, `vchmod` group rules, credentials | `platform/storage/vospace.md` |
| CADC archive access: `cadcinfo`, `cadcget`, cutouts, proprietary data, `cadc-tap`, the Python API | `platform/storage/archives.md` (new) |

## Corrections the sources forced

The skills, and in places the existing docs, were wrong on these points:

- `canfar ps --json`, `canfar auth show --json`, `canfar run`, `canfar launch`,
  `canfar logout`, `canfar storage`, and a `canfar auth login` alias do not
  exist. `tests/test_skills.py` now rejects such commands.
- The TAP executable is `cadc-tap`, not `cadctap`; its `-a` means anonymous and
  there is no asynchronous mode; its default service is `youcat`.
- `cadcget` takes exactly one identifier.
- vostools accept `--certfile` and `--token` only; `vmkdir` has `-p` and no
  `--parents`; `vsync -n` means `--nstreams`.
- `/skaha/startup.sh` is never required by the platform. It is an optional
  wrapper for `desktop-app` images only, although
  `opencadc/science-containers` docs call it a requirement for contributed
  images.
- Session Kind labels live on the registry artifact, not the project, and gate
  listing, not launching.
- `docs/platform/sessions/contributed.md` said "Do not assume a fixed port".
  The launch template fixes port 5000, which a maintainer confirmed.

Upstream issue worth reporting to `opencadc/science-platform`: `values.yaml`
documents `flexResourceRequests.<type>.memoryInGB` and `cpuCores`, while the
Deployment template reads `.memory` and `.cpu`, so the documented keys set
nothing.

## Not upstreamed on purpose

- The direct `curl --upload-file https://ws-uv.canfar.net/arc/files/...` route
  and the SSHFS instructions. `main` removed both when it rewrote transfers
  around `canfar data`. Upstream has an SFTP-only `sshd` chart (port 2222) and
  marks Cavern's `sshfs` property "NOT FUNCTIONAL"; port 64022 survives only in
  an obsolete example.
- `chmod` and `chgrp` recipes. How POSIX modes interact with VOSpace
  permissions on ARC was not verified, so the page gives diagnostics and sends
  changes through Storage Management or `vchmod`.
- "Scale out, not up" as a rule. `docs/platform/best-practices.md` already
  declines to promise that many small requests beat one large one.

## Settled by a maintainer

Operator facts no repository settles, answered by Shiny Brar on 2026-09-18 and
written into the docs:

| Question | Answer | Now in |
| --- | --- | --- |
| Does `df` on `/arc` show a quota? | No. On any path under `/arc` it shows the whole ARC filesystem, never a home or project allocation. | `platform/storage/index.md` |
| Is SFTP or SSHFS to ARC supported? | No. | `platform/storage/transfers.md`, the skill |
| DOI reviewer access and corrections | Referees get access before the DOI is minted. Published files never change; a correction adds files. | `platform/doi.md` |
| Eligibility, cost, requesting access | Canadian astronomers and collaborators, for astronomical research, not a general-purpose free cloud; email support with a CADC username and research description, or join a project's group; larger needs go to an Alliance allocation. The turnaround figure was left out. | `platform/get-started.md`, `platform/support/faq.md` |
| Storage lore | Usage figures can lag after large writes; saves and logins can fail near a full home; home is for configuration and small scripts. | `platform/storage/index.md` |
| Sharing defaults | ARC project directories are private to the group; public release is a world-readable Vault node. | `platform/permissions.md` |
| Group Management search | By username or full name. Administrators manage membership only, as the docs already said. | `platform/permissions.md` |
| Do platform images ship the client? | Yes, such as `skaha/astroml`, at times a release or two behind. | `client/advanced-examples.md`, the skill |
| Contributed applications | They must serve on port 5000. | `platform/sessions/contributed.md` |

Still open: whether the Science Portal offers Session renewal. The Server API
does and the `canfar` client does not, which is what `limits.md` says.

## Guidance kept in the skill

Answering for the audience in front of you, preferring the live Server's
answer to a documented default, and waiting for explicit instruction before an
irreversible action such as publishing a DOI are agent decision rules. They
live in `skills/canfar`, not in the user docs.
