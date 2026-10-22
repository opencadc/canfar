# Issue Trackers: Jira and GitHub Issues

You can track issues, product requirements documents (PRDs), specifications,
and implementation decisions through either route:

- **Jira:** `herzberg.atlassian.net`, project `CADC`. Retain the `CANFAR` label
  on CANFAR work. Issue keys look like `CADC-15643`.
- **GitHub Issues:** the `opencadc/canfar` repository. Reference issues by their
  repository URL or `opencadc/canfar#NUMBER`. Use the existing `PRD` label for PRDs.

## Choose the tracker

- Follow the user's explicit choice. Otherwise, use the tracker identified by
  the issue key, issue URL, or existing parent PRD.
- Keep follow-up work in the same tracker unless the user requests otherwise.
  If the destination is still unclear, ask which tracker to use before publishing.
- Search for existing work before creating an issue. Read linked records in
  either tracker. If work spans both, cross-link the records and identify which
  holds the authoritative specification and decisions; avoid duplicate specs
  that can drift apart.

## Read and write work items

- For Jira, use an available Atlassian/Jira connector and the full issue key.
  Create or update CANFAR work in `CADC`, preserving existing labels when adding
  `CANFAR`.
- For GitHub, use an available GitHub connector or `gh` with the explicit
  `opencadc/canfar` repository. Preserve unrelated existing labels.
- Read the description, acceptance criteria, linked work, and relevant decisions
  before implementing an issue from either tracker.
- Translate canonical triage roles through [Triage Labels](triage-labels.md).
  Inspect available Jira transitions or GitHub labels before updating triage.
- If access to the selected tracker is unavailable, request the relevant issue
  text or prepare a clearly marked local draft. Report publication as pending;
  do not silently switch trackers or claim that a local draft is a published issue.

## Skill conventions

"Publish to the issue tracker" means publish to the selected Jira or GitHub
destination. "Fetch the relevant ticket" means read the issue identified by its
key or repository reference. Use that tracker's relationships for parent work
and dependencies when the requested workflow needs them.

Local review reports and working drafts can support work in either tracker;
keep them clearly identified as supporting artifacts. Do not introduce local
Markdown tickets, ADRs, or RFCs as another source of truth unless the user
explicitly requests that change in convention.
