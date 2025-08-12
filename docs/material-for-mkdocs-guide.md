# Material for MkDocs – Practical Guide

This guide shows how to use Material for MkDocs effectively in this repo:
authoring content, enabling features, and adding light styling to produce
clean, readable, and beautiful documentation.

## Quick Start

- Install: `uv sync --dev` (project already includes Material and extensions).
- Serve locally: `uv run mkdocs serve` then open the printed URL.
- Build: `uv run mkdocs build` (output to `site/`).

## Anatomy of a Page

- Title: first level `# Heading` becomes the page title.
- Front matter: optional metadata via a YAML block at the top.
- Sections: use `##` and below for a sensible outline (keep to 3–4 levels).
- TOC: generated from headings; keep titles short and action‑oriented.

Example:

```markdown
---
title: Working with Sessions
description: Common tasks and patterns for sessions
---

# Working with Sessions

## Create a session
...
```

## Admonitions (Callouts)

Admonitions highlight information with semantic blocks. Prefer short titles and
one clear message per block.

- Basic: `!!! note`, `!!! tip`, `!!! warning`, `!!! danger`, `!!! info`.
- Collapsible: add `+` → `???+ note "Title"`.
- Nested content: indent further paragraphs and lists.

Examples:

```markdown
!!! tip "Quick path"
    Use `cf login` to authenticate non‑interactively in CI.

??? warning "Long‑running operations"
    Large image exports can take minutes. Prefer async workflows.

!!! note "See also"
    Related: [Quick Start](quick-start.md), [Images](images.md).
```

## Tabs and Content Switching

Use tabs to show variations (OS, language, CLI/API) without duplicating pages.

```markdown
=== "CLI"
    ```bash
    cf images list --project demo
    ```

=== "Python"
    ```python
    from canfar import Client
    Client().images().list(project="demo")
    ```
```

Guidelines:

- Keep tab labels short (1–2 words). 
- Order tabs from most common → advanced. 
- Make each tab self‑contained (no cross‑references between tabs).

## Code Blocks and Highlighting

- Fence code with language: ```python, ```bash, ```yaml for syntax.
- Add line highlights with `{hl_lines="1 3"}` and annotations via Material’s
  code annotations feature.

```python hl_lines="1 3"
from canfar import Client  # highlight
client = Client()
client.images().list()
```

Inline code: use backticks `like_this` for option names, commands, and files.

## Keyboard Keys and Badges

- Keys: `++ctrl+c++`, `++enter++` using `pymdownx.keys`.
- Badges: use inline HTML for small status chips when helpful.

```markdown
Press ++ctrl+c++ to stop the server.

<span class="badge success">stable</span>
<span class="badge warning">beta</span>
```

Minimal CSS for badges is provided below in Styling.

## Lists, Tasks, and Definitions

- Task lists: `- [ ]` unchecked, `- [x]` checked (rendered with custom boxes).
- Definition lists:

```markdown
Feature
:  Short description of what it does
```

## Images, Figures, and Grids

- Add alt text and concise captions; prefer SVG/PNG.
- Use attribute lists to set width/alignment.

```markdown
![Sequence diagram](img/flow.svg){ width="600" }
```

Display related content in responsive columns with the grid utility:

```markdown
<div class="grid cards">

-   :material-console: **CLI**

    Quick one‑liners and scripts

-   :material-language-python: **Python API**

    Full control in applications

</div>
```

## Links and Cross‑References

- Relative links: `[Images](images.md)`; use stable slugs.
- Section links: `[Workflow](quick-start.md#workflow)`.
- Repo links: `#123` and `user/repo#123` auto‑linked via `pymdownx.magiclink`.

## Tables and Formatting

- Keep tables narrow; prefer lists where possible.
- Align numeric columns right; use concise headers.
- Avoid nesting complex Markdown inside tables.

## Navigation and Structure

- Organize pages under clear sections in `mkdocs.yml/nav`.
- Use index pages as introductions with links to key tasks.
- Avoid deep nesting; prefer fewer, longer pages with strong headings.

## Search and Metadata

- Add front‑matter `description:` for better search snippets.
- Use specific headings and keywords that match user intents.

## Theming and Styling

Light, incremental styling can improve readability without departing from the
theme. Add overrides to `docs/stylesheets/overrides.css` and reference it via
`extra_css` in `mkdocs.yml`.

1) Create `docs/stylesheets/overrides.css` and add rules like:

```css
/* Admonition title weight */
.md-typeset .admonition-title { font-weight: 600; }

/* Compact code blocks */
.md-typeset pre > code { line-height: 1.3; }

/* Simple badges */
.badge { display: inline-block; padding: .1rem .4rem; border-radius: .25rem; font-size: .75rem; }
.badge.success { background: #2e7d32; color: #fff; }
.badge.warning { background: #f9a825; color: #000; }
.badge.info { background: #0288d1; color: #fff; }
```

2) Reference it in `mkdocs.yml`:

```yaml
extra_css:
  - stylesheets/asciinema-player.css
  - stylesheets/overrides.css
```

Tip: Keep CSS small and focused; avoid overriding core layout.

## Icons and Emojis

Material ships with a rich icon set via `:material-...:` syntax.

```markdown
:material-information-outline: Info  :material-alert: Alert  :material-rocket: Launch
```

Use sparingly to improve scanning, not decoration.

## Versioning and Page Status

- This repo uses `mike` (see `extra.version`). Prefer neutral language and
  avoid hard‑coding version numbers in text.
- For legacy content, add a brief banner using an admonition at the top.

```markdown
!!! warning "Applies to v1 only"
    This page documents the v1 API. See [latest](../latest/).
```

## Authoring Tips

- Write task‑first headings ("Create a session" not "Sessions").
- Keep paragraphs short (1–3 sentences). Lead with outcomes.
- Prefer examples near every concept; verify that all code runs.
- Use consistent terminology with the CLI and API reference.

## Lint, Build, and Preview

- Preview: `uv run mkdocs serve` for live reload.
- Check links: `uv run mkdocs build` (look for warnings in output).
- CI: ensure new pages are linked in `nav` to avoid orphans.

## Common Snippets

Copy/paste and adapt as needed.

Admonition with steps:

```markdown
!!! tip "Three quick checks"
    1. Headings form a clear outline
    2. Each section has an example
    3. Page appears in the sidebar nav
```

CLI/Python tabs:

```markdown
=== "CLI"
    ```bash
    cf status
    ```

=== "Python"
    ```python
    from canfar import Client
    Client().status()
    ```
```

Inline callouts:

```markdown
Use `--help` for options and :material-book-information-outline: to see docs.
```

—

When in doubt, keep it simple: clear headings, short paragraphs, helpful
admonitions, and runnable examples make the biggest difference.

