from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def read_workflow(name: str) -> dict:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text())
    return workflow["on"] if "on" in workflow else workflow[True]


def run_commands(name: str) -> list[str]:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text())
    return [
        step["run"]
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if "run" in step
    ]


def test_pull_requests_use_the_fast_suite_for_maintained_branches():
    events = read_workflow("ci.yml")
    commands = "\n".join(run_commands("ci.yml"))

    assert set(events["pull_request"]["branches"]) == {"main", "feat/interfaces"}
    assert "paths-ignore" not in events["pull_request"]
    assert 'uv run pytest -m "not slow" tests' in commands
    assert not any(
        line.strip().startswith("uv run pytest") and '-m "not slow"' not in line
        for line in commands.splitlines()
    )


def test_full_suite_is_limited_to_merged_code_prs_into_main():
    events = read_workflow("full-tests.yml")
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "full-tests.yml").read_text()
    )
    commands = "\n".join(run_commands("full-tests.yml"))

    assert events["pull_request"] == {
        "types": ["closed"],
        "branches": ["main"],
        "paths": ["canfar/**", "tests/**"],
    }
    assert "github.event.pull_request.merged == true" in workflow["jobs"]["tests"]["if"]
    assert (
        "github.event.pull_request.base.ref == 'main'"
        in workflow["jobs"]["tests"]["if"]
    )
    assert "uv run pytest" in commands
    assert '-m "not slow"' not in commands
