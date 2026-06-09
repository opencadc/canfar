# Domain Docs

Engineering skills should consume CANFAR domain docs before architecture, diagnosis, TDD, or issue-writing work.

## Layout

This repo currently has one domain glossary:

- `CONTEXT.md` at the repository root is the domain glossary.
- Specs and decisions are Jira-first; do not create ADR/RFC files as the source
  of truth unless the user explicitly asks.

## Consumer Rules

- Read `CONTEXT.md` before naming domain concepts in issues, plans, tests, or architecture reviews.
- Use glossary vocabulary exactly. Do not drift from **Authentication**, **Authentication Record**, **Science Platform Server**, **Server Selection**, **Session**, **Container Image**, or other defined terms.
- Keep `CONTEXT.md` implementation-free. It is a glossary, not a spec.
- If a concept is missing or overloaded, use `grill-with-docs` to resolve the term and update `CONTEXT.md`.
- If a proposal contradicts an existing Jira decision, surface that conflict explicitly.
