# Platform agent skills

Plain-language agent skills for the CANFAR Science Platform (sessions, storage,
groups, CLI, Python client). They live in `skills/` at the repository root.

Install:

```bash
npx skills add opencadc/canfar
```

After editing a skill or `catalog.json`:

```bash
python3 scripts/validate_skills.py
```

These guides are for coding agents. Human documentation remains the MkDocs site.
Do not treat a chart default as a live-site allocation; discover with
`canfar auth show`, `canfar server ls`, and the Science Portal.
