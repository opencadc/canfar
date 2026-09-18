"""The docs build publishes an index and Markdown sources for coding agents."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).parents[1]
HOOK = ROOT / "docs" / "hooks" / "llmstxt.py"


def _hook() -> Any:
    spec = importlib.util.spec_from_file_location("llmstxt_hook", HOOK)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _page(title: str | float, src_uri: str) -> SimpleNamespace:
    return SimpleNamespace(
        is_page=True, title=title, file=SimpleNamespace(src_uri=src_uri)
    )


def _section(title: str, *children: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(is_section=True, title=title, children=list(children))


def _navigation() -> list[SimpleNamespace]:
    return [
        _page("Home", "index.md"),
        _section(
            "Platform",
            _page("Overview", "platform/index.md"),
            _section("Sessions", _page("Batch", "platform/sessions/batch.md")),
            _section("Releases", _page(2026.2, "releases/2026-2.md")),
        ),
        SimpleNamespace(is_link=True, title="Report", url="https://example.test"),
    ]


def test_render_groups_pages_by_top_level_section() -> None:
    text = _hook().render("CANFAR", "Science Platform", _navigation())

    assert text.startswith("# CANFAR\n\n> Science Platform\n")
    assert "## Home\n\n- [Home](index.md)\n" in text
    assert (
        "## Platform\n\n"
        "- [Overview](platform/index.md)\n"
        "- [Sessions / Batch](platform/sessions/batch.md)\n"
        "- [Releases / 2026.2](releases/2026-2.md)\n"
    ) in text
    assert "example.test" not in text


def test_post_build_publishes_index_and_markdown_sources(tmp_path: Path) -> None:
    docs, site = tmp_path / "docs", tmp_path / "site"
    (docs / "platform" / "sessions").mkdir(parents=True)
    (docs / "releases").mkdir()
    (docs / "releases" / "2026-2.md").write_text("# 2026.2\n")
    (docs / "index.md").write_text("# Home\n")
    (docs / "platform" / "index.md").write_text("# Overview\n")
    (docs / "platform" / "sessions" / "batch.md").write_text("# Batch\n")
    site.mkdir()
    config = {
        "docs_dir": str(docs),
        "site_dir": str(site),
        "site_name": "CANFAR",
        "site_description": "Science Platform",
    }
    hook = _hook()

    hook.on_nav(SimpleNamespace(items=_navigation()))
    hook.on_post_build(config)

    assert (site / "platform" / "sessions" / "batch.md").read_text() == "# Batch\n"
    assert "(platform/sessions/batch.md)" in (site / "llms.txt").read_text()


def test_mkdocs_registers_the_hook() -> None:
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    assert "hooks:\n  - docs/hooks/llmstxt.py\n" in config
    assert "  hooks/**\n" in config
