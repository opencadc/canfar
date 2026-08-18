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


def test_reusable_tests_preserve_fast_and_credentialed_commands():
    workflow = load_workflow("reusable-tests.yml")
    events = workflow_events(workflow)
    commands = "\n".join(run_commands(workflow))

    assert events["workflow_call"]["inputs"]["full-suite"] == {
        "default": False,
        "required": False,
        "type": "boolean",
    }
    assert set(events["workflow_call"]["secrets"]) == {
        "CANFAR_BASEURL",
        "CANFAR_USERNAME",
        "CANFAR_PASSWORD",
        "CODECOV_TOKEN",
    }
    assert 'uv run pytest -m "not slow" tests' in commands
    assert 'CANFAR_TEST_HOME="$HOME" uv run pytest' in commands
    assert "uv run cadc-get-cert" in commands
    assert "CANFAR credentials are required for the full test suite" in commands
    assert "rm -rf ~/.ssl/" in commands

    fast_step = next(
        step
        for step in workflow["jobs"]["tests"]["steps"]
        if step.get("name") == "Run fast test suite"
    )
    full_step = next(
        step
        for step in workflow["jobs"]["tests"]["steps"]
        if step.get("name") == "Run full test suite"
    )
    verify_step = next(
        step
        for step in workflow["jobs"]["tests"]["steps"]
        if step.get("name") == "Verify CANFAR credentials"
    )
    login_step = next(
        step
        for step in workflow["jobs"]["tests"]["steps"]
        if step.get("name") == "Login to CANFAR"
    )
    cleanup_step = next(
        step
        for step in workflow["jobs"]["tests"]["steps"]
        if step.get("name") == "Remove CANFAR Certificate"
    )
    assert fast_step["if"] == "${{ !inputs.full-suite }}"
    assert full_step["if"] == "${{ inputs.full-suite }}"
    assert verify_step["if"] == "${{ inputs.full-suite }}"
    assert login_step["if"] == "${{ inputs.full-suite }}"
    assert cleanup_step["if"] == "${{ always() && inputs.full-suite }}"
    assert '-m "not slow"' not in full_step["run"]


def test_release_and_edge_delegate_to_one_container_build_contract():
    release = load_workflow("release.yml")
    edge = load_workflow("edge.yml")

    assert workflow_events(release) == {
        "repository_dispatch": {"types": ["release-build"]},
    }
    assert workflow_events(edge) == {
        "repository_dispatch": {"types": ["edge-build"]},
    }

    release_job = release["jobs"]["release-build"]
    edge_job = edge["jobs"]["edge-build"]
    assert release_job["uses"] == "./.github/workflows/reusable-container.yml"
    assert edge_job["uses"] == "./.github/workflows/reusable-container.yml"
    assert (
        release_job["permissions"]
        == edge_job["permissions"]
        == {
            "packages": "write",
            "attestations": "write",
            "id-token": "write",
        }
    )
    assert release_job["with"]["checkout-ref"] == (
        "${{ github.event.client_payload.tag_name }}"
    )
    assert "checkout-ref" not in edge_job["with"]
    assert release_job["with"]["image-version"] == (
        "${{ github.event.client_payload.tag_name }}"
    )
    assert edge_job["with"]["image-version"] == "edge"
    assert release_job["with"]["image-description"] == (
        "Python Client for CANFAR Science Portal"
    )
    assert edge_job["with"]["image-description"] == (
        "Python Client for CANFAR Science Platform"
    )
    assert release_job["with"]["image-tags"].strip().endswith(":latest")
    assert edge_job["with"]["image-tags"].strip().endswith(":edge")


def test_reusable_container_preserves_build_and_attestation_guards():
    workflow = load_workflow("reusable-container.yml")
    events = workflow_events(workflow)
    job = workflow["jobs"]["container-build"]
    steps = {step["name"]: step for step in job["steps"]}

    assert set(events["workflow_call"]["inputs"]) == {
        "checkout-ref",
        "client-payload",
        "image-description",
        "image-tags",
        "image-version",
    }
    assert workflow["permissions"] == {"contents": "read"}
    assert job["permissions"] == {
        "packages": "write",
        "attestations": "write",
        "id-token": "write",
    }
    assert steps["Build & Push Docker Image"]["uses"].startswith(
        "docker/build-push-action@"
    )
    build_with = steps["Build & Push Docker Image"]["with"]
    assert build_with["platforms"] == "linux/amd64,linux/arm64"
    assert build_with["provenance"] == "mode=max"
    assert build_with["sbom"] is True
    assert build_with["push"] is True

    attest = steps["Attest GHCR Container Image"]
    assert attest["uses"].startswith("actions/attest-build-provenance@")
    assert attest["with"]["push-to-registry"] is True
    assert attest["with"]["subject-digest"] == "${{ steps.build.outputs.digest }}"


def test_pull_requests_use_the_fast_suite_for_maintained_branches():
    workflow = load_workflow("ci.yml")
    events = workflow_events(workflow)

    assert set(events["pull_request"]["branches"]) == {"main", "feat/interfaces"}
    assert "paths-ignore" not in events["pull_request"]
    job = workflow["jobs"]["tests"]
    assert job["uses"] == "./.github/workflows/reusable-tests.yml"
    assert job["with"] == {"full-suite": False}
    assert job["needs"] == "pre-commit-checks"
    assert job["secrets"] == {
        "CODECOV_TOKEN": "${{ secrets.CODECOV_TOKEN }}",
    }


def test_full_suite_is_limited_to_merged_code_prs_into_main():
    workflow = load_workflow("full-tests.yml")
    events = workflow_events(workflow)

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
    assert workflow["jobs"]["tests"]["uses"] == "./.github/workflows/reusable-tests.yml"
    assert workflow["jobs"]["tests"]["with"] == {"full-suite": True}
    assert workflow["jobs"]["tests"]["secrets"] == {
        "CANFAR_BASEURL": "${{ secrets.CANFAR_BASEURL }}",
        "CANFAR_USERNAME": "${{ secrets.CANFAR_USERNAME }}",
        "CANFAR_PASSWORD": "${{ secrets.CANFAR_PASSWORD }}",
        "CODECOV_TOKEN": "${{ secrets.CODECOV_TOKEN }}",
    }
