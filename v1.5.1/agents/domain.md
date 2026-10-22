# Domain Docs

Read the domain documentation before architecture, diagnosis, test design,
implementation planning, or issue-writing work.

## Single-context layout

- `CONTEXT.md` at the repository root is the domain glossary for CANFAR.
- Specifications, PRDs, and implementation decisions live in the selected Jira
  or GitHub work item; see [Issue Trackers](issue-tracker.md). Follow links between
  trackers and respect the identified authoritative record for each piece of work.
- Existing records under `docs/agents/adrs/` provide supporting decision
  context. Read records relevant to the change and verify their implementation
  and release claims against current code and the relevant tracker records.
- `docs/agents/architecture.md` maps the implementation. Dated research and
  review reports under `docs/agents/` are evidence from their recorded revision.

This repository uses one glossary. It does not need a `CONTEXT-MAP.md` or a
parallel `docs/adr/` tree. Create new ADR/RFC files as authoritative decisions
only when the user explicitly requests that change in convention.

## Consumer rules

- Use the glossary's vocabulary when naming concepts in issues, plans, tests,
  and reviews: **Authentication**, **Authentication Record**, **Science Platform
  Server**, **Server Selection**, **Session**, **Container Image**, and other
  defined terms.
- Keep `CONTEXT.md` implementation-free. It names domain concepts and their
  relationships; it is not a specification or module map.
- If a concept is missing or overloaded, use `grill-with-docs` and
  `domain-modeling` to resolve the term before updating the glossary.
- Surface conflicts with an existing Jira, GitHub, or repository decision
  record explicitly. Do not silently supersede a decision or assume an old
  report describes the current implementation.
- If a supporting document does not exist, continue with the available
  context. Do not scaffold missing ADRs or context files just to satisfy a
  generic skill template.
