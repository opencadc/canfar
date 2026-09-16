# Documentation refinement validation

Validated on 16 September 2026 against the local implementation. This record
covers navigation continuity, the main user journeys, and documented client
interfaces. It is dated evidence, not a guarantee about a deployed service.

## Comparison points

- Work started at branch commit 90e99715 on feat/interfaces.
- Main: 56781bff330b5a6b1d3b2fe5b207333f37bc3e61.
- Previous published client: v1.4.1,
  d47c78e87ea98bb9b81cb2924812a52a1960de02 (11 June 2026).
- Public-page comparisons exclude dated engineering records under docs/agents.

The familiar Home, Platform, Client, Contribute, and About navigation is
restored. Releases remains under Platform; What's New remains under Client.
One duplicate authentication navigation entry was removed because Material
rendered a duplicate table-of-contents ID on that page.

Twenty ALMA compatibility pages retain their old paths and point to maintained
tasks. Existing Markdown headings from both comparison points remain available
through native headings or static compatibility anchors. Retired advice points
to its maintained replacement; the old SSHFS procedure is not reinstated.

## User journeys

The home page now leads to starting a Session, transferring data, or automating
an analysis. The browser route still needs no client installation. Quota
requests, archive URL-list downloads, Desktop fonts, and clipboard guidance
retain practical tasks from the old corpus.

Client setup, the landing page, the Python tutorial, common examples, and the
batch guide use equivalent Sync Python and Async Python tabs. The instructions
show script entrypoints and explain notebook use, accepted IDs, readiness,
persistent outputs, and scoped deletion.

The advanced guide now works through a FITS-header summary pipeline: fixed
input manifest, recorded image, one-worker testing, accepted-ID records,
bounded monitoring, output verification, recovery, and cleanup. The workshop
uses a saved manifest and small replica count, links to the complete pipeline,
and makes its unreleased client requirement visible.

What's New and migration guidance retain the distinction between features
already on main, branch interface changes, and v1.4.1. Platform release
numbering stays separate from client package versions. The CANFAR operations
skill remains consistent with the checked CLI and Python interfaces.

## Code and documentation alignment

Checked the documented Session operations and signatures, request validation,
login and explicit server selection, storage credential ownership, configuration
editing, machine-output options, logging, and distributed helpers.

Corrections include:

- storage credentials come from the storage service's owning server;
- an empty runtime token still allows an explicit runtime certificate;
- the helper's nonpositive-total error depends on a positive replica index;
- HTTP inactivity timeouts do not extend admission or image pulling after a
  creation request is accepted;
- creation acceptance and a successful deletion request are distinct from
  application readiness and confirmed disappearance.

The CLI creation-error hint and helper docstring now reflect those same
contracts. No execution behavior or API signature changed.

## Validation results

| Check | Result |
| --- | --- |
| Ruff | Passed |
| ty over canfar | Passed |
| Focused docs, helper, create, Session read, and storage tests | 104 passed |
| Deterministic non-slow suite | 844 passed |
| MkDocs build | Passed |
| Python fenced examples | All 78 compiled; 90 public API calls checked against signatures |
| Literal Session creation examples | 15 requests validated against CreateRequest |
| CLI examples | 251 parsed against current command definitions without invoking callbacks |
| Session example execution | 22 snippets ran through actual clients with HTTPX MockTransport |
| Pipeline smoke check | Passed with synthetic FITS files and mocked service responses |
| Built-site link checks | No missing internal targets or fragments; no duplicate HTML IDs |
| Main compatibility | All 85 public Markdown paths and 1,085 source-heading IDs retained |
| v1.4.1 compatibility | All 82 public Markdown paths and 1,043 source-heading IDs retained |

The workshop's explicit IMAGE_NAME placeholder was excluded from literal image
validation. Command grammar is marked as text rather than presented as a
runnable shell command.

The pipeline smoke check exercised partial and total submission failures,
missing info responses, terminal errors, polling expiry, preserved completed
outputs, recovery, attempt overwrite protection, malformed-output rejection,
and cleanup restricted to recorded IDs. All requests used a local mock
transport; no remote Sessions were created or deleted.

Browser checks covered the home and client pages at desktop width, the account
bookmark and Python tutorial at 390-pixel mobile width, keyboard tab switching,
and linked tab selection throughout the tutorial. Review findings about ALMA
destinations and the CLI timeout hint were corrected and independently closed.

## Reproduce the project checks

Run these from the repository root:

~~~bash
rtk proxy uv run --no-sync ruff check . --no-cache
rtk proxy uv run --no-sync ty check canfar
rtk proxy uv run --no-sync pytest tests -m "not slow" --no-cov -q -o cache_dir=/tmp/canfar-pytest-cache
rtk proxy uv run --no-sync --group docs mkdocs build --site-dir /tmp/canfar-docs-implementation-site
~~~

Set UV_CACHE_DIR=/tmp/canfar-uv-cache if needed. The one-off compatibility,
example, and workflow verification scripts and JSON evidence are under
/tmp/canfar-docs-review-2026-09-16 in the implementation environment.

## Limits

The build emitted the existing contributor-token warning and Material advisory.
Neither prevented the build. The checks did not exercise authenticated live
services, confirm every image's installed software, crawl external websites, or
publish a documentation deployment.

Compatibility was checked in generated local HTML against source Markdown
headings. It does not establish that every historical generated API-symbol
anchor or hosted version prefix resolves on GitHub Pages. Existing historical
version deployments were not rewritten.
