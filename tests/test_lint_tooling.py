"""Characterization tests guarding the lint-tooling consolidation (issue #130).

Ruff is the single linter source of truth. Tooling that ruff already subsumes is
removed so configuration cannot drift back into a second, redundant linter:

* the dead ``[tool.bandit]`` and ``[tool.vulture]`` sections leave ``pyproject``
  (ruff ``S`` covers bandit, ``ERA`` covers eradicate/dead code);
* the ``pyupgrade``, ``radon``, ``actionlint`` and ``interrogate`` hooks leave
  ``.pre-commit-config.yaml`` (ruff ``UP`` covers pyupgrade, ``D`` enforces
  docstring presence/style more strictly than interrogate's coverage gate).

These tests pin both halves of the change: the redundant tooling is gone, *and*
ruff still selects the rule families that catch the equivalent issues. The
matching dev dependencies (``bandit``/``vulture``) are dropped too, so they
cannot silently linger as an installed-but-unused second linter.
"""

from __future__ import annotations

from pathlib import Path

import toml
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_PYPROJECT = _ROOT / "pyproject.toml"
_PRE_COMMIT = _ROOT / ".pre-commit-config.yaml"


def _pyproject() -> dict:
    return toml.loads(_PYPROJECT.read_text(encoding="utf-8"))


def _pre_commit_repos() -> list[str]:
    config = yaml.safe_load(_PRE_COMMIT.read_text(encoding="utf-8"))
    return [repo.get("repo", "") for repo in config["repos"]]


def _pre_commit_hook_ids() -> set[str]:
    config = yaml.safe_load(_PRE_COMMIT.read_text(encoding="utf-8"))
    return {
        hook.get("id", "") for repo in config["repos"] for hook in repo.get("hooks", [])
    }


def test_redundant_tool_sections_removed() -> None:
    """``[tool.bandit]`` and ``[tool.vulture]`` are gone from pyproject."""
    tools = _pyproject().get("tool", {})
    assert "bandit" not in tools
    assert "vulture" not in tools


def test_ruff_remains_configured() -> None:
    """Ruff stays the single configured linter source of truth."""
    assert "ruff" in _pyproject().get("tool", {})


def test_ruff_selects_subsuming_rule_families() -> None:
    """Ruff still selects the rules that cover the removed tooling."""
    selected = set(_pyproject()["tool"]["ruff"]["lint"]["select"])
    # S -> bandit, ERA -> vulture/dead code, UP -> pyupgrade, D -> interrogate.
    assert {"S", "ERA", "UP", "D"} <= selected


def test_redundant_precommit_hooks_removed() -> None:
    """pyupgrade, radon, actionlint and interrogate hooks are removed."""
    hook_ids = _pre_commit_hook_ids()
    for removed in ("pyupgrade", "radon", "actionlint", "interrogate"):
        assert removed not in hook_ids


def test_redundant_precommit_repos_removed() -> None:
    """The external repos backing the removed hooks are gone too."""
    repos = _pre_commit_repos()
    for fragment in ("pyupgrade", "actionlint", "interrogate"):
        assert not any(fragment in repo for repo in repos)


def test_ruff_precommit_hook_retained() -> None:
    """The ruff pre-commit hook stays wired in."""
    assert "ruff" in _pre_commit_hook_ids()
    assert any("ruff-pre-commit" in repo for repo in _pre_commit_repos())


def test_redundant_linter_dev_dependencies_removed() -> None:
    """The bandit and vulture dev dependencies are no longer installed."""
    dev_deps = _pyproject()["dependency-groups"]["dev"]
    names = {dep.split(">=")[0].split("[")[0].strip() for dep in dev_deps}
    assert "bandit" not in names
    assert "vulture" not in names
    assert "ruff" in names
