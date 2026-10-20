# The CANFAR skill

`skills/canfar/` is the one skill published for users' coding agents. Users
install it with `npx skills add opencadc/canfar --skill canfar`; see
[CANFAR Agent Skill](../platform/agent-skill.md) for installation and invocation
in each agent. It is separate from `AGENTS.md`, which guides agents working on
this repository.

## How it stays true

Each kind of knowledge has one source of truth, and the skill copies as little
of it as possible:

| Knowledge | Source of truth | What the skill does |
| --- | --- | --- |
| Flags, options, signatures | The user's installed `canfar --help` and `help()` | Tells the agent to read them first |
| Platform topics: storage, images, permissions, DOI | `docs/` | Points at the page in its topic table |
| Workflows, completion criteria, gotchas | `skills/canfar/` | States them, pinned by tests |

`tests/test_skills.py` runs with the deterministic suite and fails when:

- a `canfar` command in the skill, or in the user docs, names a command or
  option the CLI rejects;
- a Python example imports a missing name, calls a missing method, or passes an
  argument the API lacks;
- a dotted API name in the skill's prose does not resolve;
- the skill's machine-output list differs from the commands that own `-o`;
- a docs URL, anchor, or relative link in the skill has no target.

A change to the CLI or Python surface therefore updates the docs and the skill
in the same pull request.

## Which docs the skill links

`npx skills add` installs the skill from `main`, so the skill links the `edge`
docs, which `mike` deploys from `main`. `latest` is the last release and can
describe an older interface, or lack a page the skill points at.

`docs/hooks/llmstxt.py` runs after every build. It writes `llms.txt`, an index
of the navigation, and copies each page's Markdown source into the site at its
source path, so `platform/doi.md` is served beside `platform/doi/`. Agents read
the text the site was built from, and relative links between pages still work.
The hook has no dependencies beyond MkDocs; `tests/test_docs_llmstxt.py`
covers it.

## Editing the skill

- Put new platform knowledge in `docs/` and add its page to the topic table.
  Human readers need it too, and the docs are reviewed by the people who run
  the platform.
- Keep `SKILL.md` to what every request needs. Material for one kind of request
  belongs in `skills/canfar/references/`, reached from the routing table.
- State the command that exists. The command test has no allowance for naming
  removed commands in the skill.
- End each step on a condition the agent can observe, using the skill's three
  states: accepted, Running, verified.

```bash
uv run pytest tests/test_skills.py --no-cov -n0
```
