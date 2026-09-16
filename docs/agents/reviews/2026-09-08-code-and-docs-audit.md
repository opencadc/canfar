# CANFAR code and documentation review

## Implementation follow-up — September 9, 2026

The findings below were implemented on `feat/interfaces`, using
`d4af2d9d734dcef22f9ef16b2a6b927af1df5e47` as the implementation baseline.
The original audit is retained below as historical evidence; its line numbers
refer to that baseline.

| Finding | Implementation |
| --- | --- |
| C1 | One OIDC credential initializer in `canfar.auth.oidc`, shared by CLI, sync Python, and async Python login |
| C2 | Workflow steps indexed once; incidental image-description assertions removed; security and execution checks retained |
| Ranked cuts | Direct Pydantic serialization, inline Session query/event dictionaries, and unused free editor helper removed |
| D1 | Unreleased updates, release/main/branch comparison, exact upgrade mappings, and separate release/development installation instructions |
| D2 | Complete browser notebook launch/run/save/delete tutorial and browser entry points for all interactive Session guides |
| D3 | Browser uploads, ZIP/URL/HTML downloads, verification steps, and links to CLI transfers |
| D4 | Group creation, membership, administrators, separate allocation requests, and directory access verification |
| D5 | Publication packages and checkpoints explicitly saved in `/arc` or the DPS directory |
| D6 | CASA calibration, imaging, then CARTA inspection of image products |
| D7 | Python identity/server selection after login; notebook selection offloaded with `asyncio.to_thread`; separate storage-owner authentication |
| D8 | Runtime environment-variable migration and scoped manual configuration recovery preserving the old file |
| D9 | Source docstrings describe logging and server-dependent flexible resources |
| Organization | Task-oriented navigation preserves every existing destination, removes duplicate authentication navigation, and adds agent guidance |
| Agent skill | Standalone `skills/canfar/SKILL.md`, including capability checks and event-loop-safe notebook selection; prepared for publication |

### Validation of the implementation

| Check | Result |
| --- | --- |
| Focused auth, CLI output, Session, editor, and workflow tests | 59 passed before and after code cleanup |
| Ruff and `ty check canfar` | Passed |
| Ruff format check on the seven changed Python files | Passed |
| Normal deterministic non-slow suite, after final ALMA correction | 844 passed |
| Complete suite in a temporary home with copied usable CADC credentials | 848 passed, 5 failed; 88.82% coverage, above the 75% gate |
| Follow-up on full-suite failures | The ALMA login-step omission was corrected. Two configuration tests failed with a populated test home and passed in the normal isolated suite. Both live lifecycle tests returned no created IDs; a focused sync retry confirmed HTTP 400 from Session creation. |
| MkDocs build | Passed; existing Git metadata/token warnings remain |
| Changed Markdown/skill code blocks | 34 Python and 66 shell blocks passed syntax checks |
| Rendered local links from changed user pages | 1,408 checked, no missing targets or anchors |
| Final independent Standards review | No remaining P0–P2 findings after correcting notebook event-loop guidance |
| Final independent Spec review | No P0–P2 findings; requirements and navigation coverage confirmed |

The full authenticated suite is **not green**. Its remaining populated-home
and live creation failures are recorded separately from the deterministic
implementation gate. No live service or test-fixture behavior was changed to
make those checks pass. The browser instructions were checked against source,
public service pages, and rendered documentation; no browser analysis,
upload, group change, or publication was performed.

Your existing `AGENTS.md` changes and two presentation artifacts were preserved.
The skill and documentation were prepared locally; neither was published.

## Original audit — September 8, 2026

The branch improves several code boundaries and makes the documentation much
shorter, but it is not ready for documentation sign-off. Two code-quality
findings and nine documentation findings remain. The documentation needs a
usable upgrade path, complete browser workflows, and corrections to several
instructions. Passing tests and a successful site build do not resolve those
content gaps.

This review applies deslop, thermo-nuclear-code-quality-review, and
ponytail-audit. Code standards and the user's documentation requirements were
reviewed independently. Findings are recommendations; no existing source,
tests, or documentation were edited. The requested `skills/canfar/SKILL.md`
was created alongside this report.

## Comparison and coverage

| Comparison | Pinned reference |
| --- | --- |
| Reviewed branch | `feat/interfaces`, `d4af2d9d734dcef22f9ef16b2a6b927af1df5e47` |
| Main | `5f95cfe72ae0852b20414ea1ebcf7d576cd41f65`; local `main`, `origin/main`, and GitHub agreed |
| Previous client release | [`v1.4.1`](https://github.com/opencadc/canfar/releases/tag/v1.4.1), `d47c78e87ea98bb9b81cb2924812a52a1960de02`, published June 11, 2026 |
| Branch comparison | `git diff main...HEAD` |
| Release comparison | `git log v1.4.1..HEAD`, release source/API inspection, and branch documentation |

The audit covered the source/module structure, dependency declarations,
relevant tests and workflows, all 65 current user-facing Markdown pages,
navigation, and all 20 deleted ALMA Markdown pages. Generated API documentation
was also inspected in the built site. Dated engineering records were treated
as historical context, not current product instructions. The existing dirty
`AGENTS.md` and two untracked presentation files were preserved.

| Measure | Main | Branch | Change |
| --- | ---: | ---: | ---: |
| User-facing Markdown pages, excluding `docs/agents/` | 85 | 65 | -20 |
| Words in those source pages, including code | 56,488 | 24,962 | -31,526 (56%) |
| Python source lines under `canfar/` | 11,120 | 11,097 | -23 |

The branch source diff is +2,122/-2,145 lines; tests are +3,214/-2,479.
These are source-file counts, not rendered-site sizes or measures of quality.
No production Python file crosses 1,000 lines. `auth/oidc.py` grows from 606 to
921 lines; `server.py` is decomposed from 962 lines into a 346-line selection
module and a 674-line discovery module. `test_server.py` grows from 1,404 to
1,524 lines, having already exceeded the threshold on main.

## Standards findings

### C1 — P2: Share OIDC credential initialization across login adapters

At `canfar/authentication.py:412-426`, the branch adds IDP discovery/issuer
checks and construction of an empty OIDC credential. The same policy already
exists at `canfar/cli/login_auth.py:171-185`. Adding required metadata or
changing credential defaults now requires coordinated edits in the library
and CLI presentation layer.

Move the initializer into the existing `canfar.auth.oidc` module, accept
`IdpInfo` alone, and use it from CLI, synchronous Python, and asynchronous
Python login. Keep their transport and presentation behavior separate. This
is duplicated domain policy, not a reason to merge the native sync and async
transports.

### C2 — P2: Test workflow guarantees without freezing display text

`tests/test_ci_workflows.py:112-117` requires release images to describe
themselves as “Science Portal” while edge images say “Science Platform”.
`tests/test_ci_workflows.py:47-71` also repeats five searches through the same
steps by display name. These new assertions make harmless editorial changes
require test changes without demonstrating an additional execution guarantee.

Remove exact prose assertions and index the steps once. Preserve checks for
credential isolation, merged-only execution, checkout selection, image tags,
and attestations. This is a test-maintainability finding, not a claim that the
workflows fail.

There is no P1 structural finding. The branch already removes substantial
scaffolding; another broad rewrite is not justified by file size alone. The
deslop pass found focused simplifications below, rather than evidence that
all defensive checks or typed boundaries should be stripped.

## Ponytail audit: ranked cuts

shrink: Remove workflow prose assertions and repeated step searches. Index once and retain execution invariants; about 20 lines. [`tests/test_ci_workflows.py:47`](../../../tests/test_ci_workflows.py)

shrink: Collapse duplicated OIDC credential initialization. One initializer in the existing protocol module; about 15 lines. [`canfar/authentication.py:412`](../../../canfar/authentication.py)

native: Delete `_serialize_payload`. Use `to_jsonable_python(data)` directly; about 14 lines, an existing opportunity. [`canfar/cli/output.py:40`](../../../canfar/cli/output.py)

yagni: Inline `_view_parameters` and `_response_event`. Use `{"view": view}` and `{session_id: response.text}`; about 10 lines introduced on this branch. [`canfar/sessions.py:66`](../../../canfar/sessions.py)

delete: Remove the free `config.editor.set_value` helper. The bound editor migration leaves no repository code, test, or documented caller; about 5 lines. [`canfar/config/editor.py:94`](../../../canfar/config/editor.py)

net: -64 lines, -0 deps possible.

Estimates are conservative, nonoverlapping, and include comments/spacing.
They include C1/C2 rather than adding to them. Native serialization was checked
with nested lists, Pydantic models, nulls, and `SecretStr`. No runtime dependency
was identified as safely removable. In particular, the supported sync/async
interfaces, distributed helpers, and delegated VOSpace implementation should
not be deleted as apparently redundant code.

## Documentation findings

### D1 — P2: Explain the upgrade from v1.4.1 and label unreleased features

`docs/client/updates.md:3-25` describes current API contracts without saying
which changed since `v1.4.1`. `docs/client/migration.md:1` still frames migration
only as `skaha` to `canfar`. Neither provides a usable transition for current
CANFAR users. Meanwhile `docs/cli/quick-start.md:7-10` installs the published
package before demonstrating the branch's new interface.

Add a clearly labeled unreleased upgrade section with before/after examples
for `--json`/`--yaml` to `-o json`/`-o yaml`, removed command aliases,
`Configuration.get_value/set_value/save` to `config.editor.get/set/save`, and
the contraction of Python storage access. Distinguish changes already merged
to main but absent from `v1.4.1`, such as `canfar data`, from changes introduced
only on this branch. Link the relevant workflows and state supported versions;
do not assign a future release number without a release decision.

The current code and package metadata still identify themselves as `1.4.1`,
so a version string alone cannot distinguish the checkout from the published
release. The new agent skill checks installed capabilities as well as version.

### D2 — P2: Restore a complete first analysis in the browser

`docs/platform/get-started.md:16-23` compresses launching into selecting a kind
and image. `docs/platform/sessions/notebook.md:17-20` refers browser users back
to command help. Main `sessions/notebook.md:23-99` explained launching,
connecting, creating a notebook, and running cells. The
[Science Portal](https://www.canfar.net/science-portal/) still has separate
launch and active-session areas.

Restore a short browser sequence: sign in, launch a notebook, wait for it,
open it, create and run a notebook, save it in persistent storage, and stop the
Session. Use current control names. Screenshots are optional; complete text
instructions are not. Keep client installation optional for this route.

### D3 — P2: Restore browser file transfer instructions

`docs/platform/storage/transfers.md:3-5` now covers only `canfar data` and
`docs/platform/storage/vospace.md:15-22` omits browser access. Main
`transfers.md:40-57,129-136` and the deleted ALMA `Using_webstorage.md:5-31`
provided upload and ZIP/URL/HTML download workflows. The
[Storage Management service](https://www.canfar.net/storage/arc/list) remains
available.

Add a browser upload/download route with a direct service link, destination
selection, completion check, and a link to CLI transfers for automation. Do
not require readers to install Python merely to move their first file.

### D4 — P2: Restore the steps for creating and managing a group

`docs/platform/permissions.md:26-30` replaces group administration with one
descriptive sentence. Main `permissions.md:89-118` contained create-group,
add-member, and add-administrator steps; the current
[group interface](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/)
still exposes these operations.

Restore those short tasks, state who can perform each, and distinguish group
membership from requesting project storage and granting access to a directory.
A new project lead should be able to follow the page without prior CADC
administration knowledge.

### D5 — P2: Correct the reversed persistence instruction

`docs/platform/doi.md:51-53` directs readers to store a package/checkpoint that
must survive **outside `/arc` or the DPS data directory**. The adjacent advice
and `docs/platform/storage/index.md` identify these as persistent destinations.
The sentence therefore directs publication data away from the intended place.

Say: “Save the package and checkpoints in `/arc` or the data directory shown
by DPS. Use `/scratch` only for temporary staging.” This is a branch-introduced
accuracy problem with a potential data-loss consequence.

### D6 — P2: Open image products, not measurement sets, in CARTA

`docs/platform/community/alma/index.md:96-99` tells users to open calibrated
measurement sets or image products in CARTA. CARTA's documented inputs are
image formats, including CASA images, FITS, HDF5 IDIA, and MIRIAD; a calibrated
measurement set is not a CASA image. See the
[official CARTA file-browser documentation](https://carta.readthedocs.io/en/latest/file_browser.html).

Restore the explicit calibration-to-imaging-to-inspection sequence. The
deleted main `ALMA_Desktop/typical_reduction.md:14-20` distinguished
`scriptForPI.py`, the calibrated output directory, and `scriptForImaging.py`.
Use the archive's version-appropriate imaging script, then inspect its image
products in CARTA. The text need not revive every old screenshot or duplicate
ALMA page.

### D7 — P2: Finish the Python login-to-Session workflow

`docs/client/get-started.md:63-79` correctly says Python login does not change
the active identity or Server, but then immediately constructs `Session()`
with saved defaults. A reader following the new SRCNet login example can
therefore send the next request to their old CADC selection, or fail because
that credential is missing.

Show selection between those steps, using `canfar.authentication.use(IDP)`
and `canfar.server.use(SELECTOR)`, or explicitly direct the reader to the CLI
selection flow. Include how to discover/select a compatible Server. State that
storage uses its owning Server's IDP independently: SRCNet login does not
authenticate default CADC `arc` and `vault` services.

### D8 — P2: Preserve environment migration and accurate reset recovery

`docs/client/migration.md:34-55` drops main's environment-variable migration
and configuration-recovery sections. There is no replacement user guide for
the `SKAHA_` to `CANFAR_` runtime overrides. These are still implemented by
`HTTPClient`'s settings prefix (`canfar/client.py:66-71`).

Restore a verified environment table and an actionable legacy-configuration
recovery procedure. Explain preserving the old file, resetting only the
identified configuration when necessary, and logging in again. Do not restore
main's inaccurate automatic `.back` backup promise:
`canfar/config/migration.py:40-64` rejects unsupported formats without
automatically backing up or rewriting them. Merely running login, as
`docs/releases/2026-2.md:25-33` suggests, does not bypass that rejection.

### D9 — P2: Include generated docstrings in the corpus correction

`canfar/sessions.py:345-351` and `:741-747` still say verbose events print to
stdout only, while the implementation logs them. The built Session and
AsyncSession pages publish those statements alongside prose correctly saying
they use `canfar.sessions` logging. Their verbose-log parameters contain the
same contradiction (`:218` and `:601`).

Correct the source docstrings and rebuild the generated reference. Check the
hard-coded flexible-allocation promise at `:281` and `:670` as part of that
pass: the guide correctly treats resource policy as Server-dependent. A
Markdown-only edit leaves the contradictory public instructions in the site.
This is existing source-doc debt still visible after the branch's reference
rewrite, not a new runtime defect.

## Feature coverage since the previous client release

This matrix distinguishes capabilities from internal refactors. Existing
features should not be advertised as new solely because their documentation
was rewritten.

| Capability/change | Since v1.4.1? | Current coverage | Required improvement |
| --- | --- | --- | --- |
| POSIX-shaped `canfar data`, configured `arc`/`vault`/`local` | Yes; already on main | CLI data and storage transfer guides | Add to the release summary with one upload/download example and boundaries |
| Recursive copy; no recursive removal or cross-source move | Part of new data surface | Explicit in `docs/cli/data.md` | Preserve these limits in release/agent guidance |
| Python `identifiers()` / `filesystem()` | Yes; main introduced storage, branch contracts it | `docs/client/data.md` is a useful canonical guide | Explain old dynamic imports/source mapping to explicit identifier/path migration |
| Directory-listing cache and explicit content staging/cache | New storage surface | Data guide distinguishes listing and content caching | Link from release summary; do not imply partial reads guarantee partial transfers |
| Native Python OIDC `login()` / `alogin()` | Yes; branch | Setup and updates pages | Complete Server Selection and separate storage authentication (D7) |
| Bound Configuration editor | Yes; branch | Setup and migration explain current methods | Add exact old-to-new method mapping and state what was removed |
| `-o/--output` replacing `--json`/`--yaml` | Yes; branch | Reference documents new syntax and supported commands | Add breaking-change notice and before/after examples (D1) |
| Removed aliases/root leaf simplification | Yes; branch | Reference lists canonical commands | Document old spellings that stop working; retain actual compatibility aliases only |
| Root log levels and optional rotating JSON Lines file | Yes; changes after release, largely already main | Logging guide covers controls, precedence, fields, diagnostics | Explain migration from older log controls and removed logging machinery |
| Configurable human Server banner | Yes; already main | Authentication/config guide and output reference | Mention the setting and script-safe output in the release summary |
| `create` domain request/dry-run/machine result contract | Changed after release | CLI reference and Python return-shape guides | Present the user benefit and partial-replica failure behavior in release notes |
| Runtime credentials and saved-refresh precedence | Changed after release | HTTPClient guide is detailed | Retain; tie behavior to the upgrade summary rather than architecture vocabulary |
| Reuse usable CADC certificates | Changed after release; main | Authentication guide | Include a brief upgrade note; no new login mode is implied |
| Sync/async Sessions, flexible/fixed resources, replicas, distributed helpers | Present in v1.4.1; contracts have refinements | Python guides and batch page | Preserve task examples; distinguish refinements such as keyword-only filter parity from new features |
| Platform 2026.2 changes | Separate platform release numbering | Historical release pages | Keep platform history distinct from unreleased client changes; archive exact deployment details when still needed |

The existing platform release pages and unchanged package changelog are not a
substitute for an unreleased client upgrade guide. Do not relabel the June
platform release to imply the branch interface was available in its package.

## Organization and language

The shorter paragraphs and descriptive headings are a substantial improvement.
The remaining organization still privileges the client implementation over a
new astronomer's tasks. In particular, Python return contracts dominate the
updates page, interactive Session pages begin with CLI commands, and the same
authentication page appears twice in Client navigation.

Use the current pages behind a clearer set of entry points:

| User task | Entry point and content |
| --- | --- |
| Start an analysis | Browser quickstart, then optional Python/CLI paths |
| Analyse in a browser | Notebook, Desktop, CARTA, Firefly, contributed apps |
| Move and save data | Browser transfers, mounted paths, CLI transfers, Python access |
| Share a project | Groups, members, administrators, storage access |
| Automate analyses | CLI/Python tutorials, headless jobs, replicas, results and cleanup |
| Build an environment | Image selection, custom builds, private registry access |
| Publish data | Prepare, verify, publish, cite |
| Get help or upgrade | Troubleshooting, current client changes, migration, separate platform history |
| Look up details | Complete CLI and Python references; agent skill |

Keep conceptual definitions close to first use: expand Canadian Astronomy Data
Centre (CADC), Identity Provider (IDP), OpenID Connect (OIDC), and Data
Publication Service (DPS); explain VOSpace as remote file storage before using
its protocol name. For routine tasks, address the reader directly. For example,
start the data page with “Use `canfar data` to copy files between your computer
and CANFAR storage,” then explain identifiers with one concrete path.

Do not restore main wholesale. It included stale automatic-backup claims,
unsupported storage/cache assumptions, duplicated examples, and stub pages.
Most deleted ALMA pages do not warrant restoration as separate pages. Recover
the useful tasks in the canonical guides, with verified text and current
interfaces. Historical deployment details belong in clearly dated material.

## Agent skill created

`skills/canfar/SKILL.md` is standalone and has valid name/description
frontmatter. It covers installed-version checks, identity and Server
Selection, Session readiness and IDs, native Python clients, replicated work,
storage ownership and paths, machine output, and scoped cleanup.

An independent offline forward test exercised a released-client batch scenario
and a notebook/OIDC/VOSpace scenario. It exposed a missing storage-owner IDP
explanation, which was added. The skill does not assume that SRCNet login
authenticates CADC storage or that the released package already has the branch
interface. It was created for later publication; no installation or publication
was performed.

## Validation and limits

| Check | Result |
| --- | --- |
| `UV_CACHE_DIR=/tmp/canfar-uv-cache uv run --no-sync ruff check . --no-cache` | Passed |
| `UV_CACHE_DIR=/tmp/canfar-uv-cache uv run --no-sync ty check canfar` | Passed |
| `UV_CACHE_DIR=/tmp/canfar-uv-cache uv run --no-sync pytest tests -m 'not slow' --no-cov -q -o cache_dir=/tmp/canfar-pytest-cache` | 844 passed in 12.45 seconds |
| `UV_CACHE_DIR=/tmp/canfar-uv-cache uv run --group docs mkdocs build --site-dir /tmp/canfar-corpus-review-site` | Passed; GitHub contributor-token/co-author warnings only for site metadata, plus the theme's general advisory |
| Python code fences in user docs and skill | All 70 compiled, allowing notebook-style top-level await; examples were not executed against a platform |
| Skill-creator `quick_validate.py skills/canfar` | Passed |

Shell commands used the repository's `rtk` prefix. Full authenticated tests,
actual Session launches, logged-in browser workflows, comprehensive external
link crawling, deployment upgrades, and publication were not performed. Public
browser surfaces and official CARTA documentation were checked for the relevant
retention/accuracy findings. A successful build establishes renderability, not
factual completeness.

Standards: 2 P2 findings, with duplicated OIDC initialization the main structural
issue. Documentation requirements: 9 P2 findings, with the reversed persistence
instruction the highest-consequence accuracy issue and the missing upgrade path
the largest release-coverage gap.
