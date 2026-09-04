#!/usr/bin/env python3
"""Validate the plugin catalog and its local skill packages."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CATALOG = ROOT / "catalog.json"
PLUGIN = ROOT / ".cursor-plugin" / "plugin.json"

# Reject AstroAI product CLI/images/skills. Install path is opencadc/canfar.
_PRODUCT_LEAK = re.compile(
    r"astroai-ray|astroai-lab|/opt/astroai|`astroai`|AstroAI|"
    r"(?<![/\w.])astroai|"
    r"\bRay\b|\$WORK",
    re.IGNORECASE,
)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def _leak_spans(text: str) -> list[str]:
    return [match.group(0) for match in _PRODUCT_LEAK.finditer(text)]


def main() -> int:
    errors = 0
    catalog = json.loads(CATALOG.read_text())
    plugin = json.loads(PLUGIN.read_text())

    directories = {path.name: path for path in SKILLS.iterdir() if path.is_dir()}
    entries = catalog.get("skills", [])
    ids = [entry.get("id") for entry in entries]

    if len(ids) != len(set(ids)):
        fail("catalog contains duplicate skill IDs")
        errors += 1
    if set(ids) != set(directories):
        fail(
            "catalog skill IDs and skill directories differ: "
            f"catalog-only={sorted(set(ids) - set(directories))}, "
            f"directory-only={sorted(set(directories) - set(ids))}"
        )
        errors += 1

    for skill_id in ids:
        if isinstance(skill_id, str) and skill_id.startswith("astroai"):
            fail(f"{skill_id}: AstroAI extension skills do not belong in this repo")
            errors += 1

    for entry in entries:
        skill_id = entry["id"]
        expected_path = f"skills/{skill_id}"
        if entry.get("path") != expected_path:
            fail(f"{skill_id}: catalog path must be {expected_path!r}")
            errors += 1

    link_pattern = re.compile(r"\[[^]]*]\((?!https?://|mailto:|#)([^)]+)\)")
    for skill_id, directory in sorted(directories.items()):
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file():
            fail(f"{skill_id}: missing SKILL.md")
            errors += 1
            continue

        text = skill_file.read_text()
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            fail(f"{skill_id}: malformed YAML frontmatter")
            errors += 1
            continue

        frontmatter = text.split("\n---\n", 1)[0][4:]
        name_match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", frontmatter)
        if not name_match or name_match.group(1) != skill_id:
            fail(f"{skill_id}: frontmatter name must match directory")
            errors += 1
        if not re.search(r"(?m)^description:\s*(?:>|>-|\S)", frontmatter):
            fail(f"{skill_id}: missing frontmatter description")
            errors += 1
        if text.count("```") % 2:
            fail(f"{skill_id}: unbalanced fenced code block")
            errors += 1

        for md in sorted(directory.rglob("*.md")):
            leaks = _leak_spans(md.read_text())
            if leaks:
                fail(f"{md.relative_to(ROOT)}: AstroAI product leak {leaks!r}")
                errors += 1

        for target in link_pattern.findall(text):
            clean_target = target.split("#", 1)[0]
            if clean_target and not (directory / clean_target).exists():
                fail(f"{skill_id}: missing local link target {target!r}")
                errors += 1

    workflow_ids = {
        included
        for workflow in catalog.get("workflows", [])
        for included in workflow.get("includes", [])
    }
    if workflow_ids != set(ids):
        fail("workflow membership must include every catalog skill exactly by ID")
        errors += 1

    for key in ("name", "version"):
        if catalog.get(key) != plugin.get(key):
            fail(f"catalog and plugin {key!r} values differ")
            errors += 1

    readme = ROOT / "README.md"
    if readme.is_file():
        leaks = _leak_spans(readme.read_text())
        if leaks:
            fail(f"README.md: AstroAI product leak {leaks!r}")
            errors += 1

    if errors:
        print(f"Validation failed with {errors} error(s).", file=sys.stderr)
        return 1
    print(f"Validated {len(directories)} skills and {len(entries)} catalog entries.")
    return 0


def _self_check() -> None:
    assert _leak_spans("npx skills add opencadc/canfar") == []
    assert _leak_spans("https://github.com/opencadc/canfar") == []
    assert _leak_spans("npx skills add astroai/canfar-skills") == ["astroai"]
    assert _leak_spans("astroai status --json") == ["astroai"]
    assert _leak_spans("AstroAI images") == ["AstroAI"]
    assert _leak_spans("see astroai-ray") == ["astroai-ray"]
    assert _leak_spans("Ray cluster") == ["Ray"]
    assert _leak_spans("cd $WORK/mylab") == ["$WORK"]


if __name__ == "__main__":
    _self_check()
    raise SystemExit(main())
