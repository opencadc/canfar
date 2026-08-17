from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def load_workflow(name: str) -> dict:
    return yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text())


def workflow_events(workflow: dict) -> dict:
    return workflow["on"] if "on" in workflow else workflow[True]


def run_commands(workflow: dict) -> list[str]:
    return [
        step["run"]
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if "run" in step
    ]


def test_pull_requests_use_the_fast_suite_for_maintained_branches():
    workflow = load_workflow("ci.yml")
    events = workflow_events(workflow)
    commands = "\n".join(run_commands(workflow))

    assert set(events["pull_request"]["branches"]) == {"main", "feat/interfaces"}
    assert "paths-ignore" not in events["pull_request"]
    assert 'uv run pytest -m "not slow" tests' in commands
    assert not any(
        line.strip().startswith("uv run pytest") and '-m "not slow"' not in line
        for line in commands.splitlines()
    )


def test_full_suite_is_limited_to_merged_code_prs_into_main():
    workflow = load_workflow("full-tests.yml")
    events = workflow_events(workflow)
    commands = "\n".join(run_commands(workflow))

    assert set(events) == {"pull_request_target"}
    assert events["pull_request_target"] == {
        "types": ["closed"],
        "branches": ["main"],
        "paths": ["canfar/**", "tests/**"],
    }
    assert "github.event.pull_request.merged == true" in workflow["jobs"]["tests"]["if"]
    assert (
        "github.event.pull_request.base.ref == 'main'"
        in workflow["jobs"]["tests"]["if"]
    )
    assert workflow["jobs"]["tests"]["env"] == {
        "CANFAR_BASEURL": "${{ secrets.CANFAR_BASEURL }}",
        "CANFAR_USERNAME": "${{ secrets.CANFAR_USERNAME }}",
        "CANFAR_PASSWORD": "${{ secrets.CANFAR_PASSWORD }}",
        "CODECOV_TOKEN": "${{ secrets.CODECOV_TOKEN }}",
    }
    assert (
        'if [ -z "${CANFAR_BASEURL}" ] || [ -z "${CANFAR_USERNAME}" ] '
        '|| [ -z "${CANFAR_PASSWORD}" ]; then'
    ) in commands
    assert "CANFAR credentials are required for the full test suite" in commands
    login_step = next(
        step
        for step in workflow["jobs"]["tests"]["steps"]
        if step.get("name") == "Login to CANFAR"
    )
    assert "if" not in login_step
    assert 'CANFAR_TEST_HOME="$HOME" uv run pytest' in commands
    assert "uv run cadc-get-cert" in commands
    assert "rm -rf ~/.ssl/" in commands
    assert '-m "not slow"' not in commands
