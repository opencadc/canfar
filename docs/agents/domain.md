# Domain Docs

Engineering skills should consume CANFAR domain docs before architecture, diagnosis, TDD, or issue-writing work.

## Layout

This is a single-context repo:

- `CONTEXT.md` at the repository root is the domain glossary.
- `docs/adr/` holds architecture decision records when they exist.

If `docs/adr/` does not exist, proceed silently. Create it only when a real ADR is needed.

## Consumer Rules

- Read `CONTEXT.md` before naming domain concepts in issues, plans, tests, or architecture reviews.
- Use glossary vocabulary exactly. Do not drift from **Authentication Context**, **Science Platform Server**, **Session**, **Container Image**, or other defined terms.
- Keep `CONTEXT.md` implementation-free. It is a glossary, not a spec.
- If a concept is missing or overloaded, use `grill-with-docs` to resolve the term and update `CONTEXT.md`.
- If a proposal contradicts an ADR, surface that conflict explicitly.

## ADR Policy

Create ADRs sparingly under `docs/adr/` only when a decision is hard to reverse, surprising without context, and based on a real trade-off.
