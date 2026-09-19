"""Publish the documentation for coding agents.

MkDocs hook. After a build it writes ``llms.txt``, an index of every page in
the navigation, and copies each page's Markdown source into the site at its
source path (``platform/doi.md`` beside ``platform/doi/index.html``). An agent
then reads the exact text the site was built from, and relative links between
pages keep working because the source layout is preserved.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

_NAVIGATION: dict[str, Any] = {}


def _pages(items: Iterable[Any], trail: tuple[str, ...] = ()) -> Iterator[Any]:
    """Yield ``(trail, page)`` for every page below navigation ``items``."""
    for item in items:
        if getattr(item, "is_section", False):
            # YAML reads a navigation title such as ``2026.2`` as a number.
            yield from _pages(item.children, (*trail, str(item.title)))
        elif getattr(item, "is_page", False):
            yield trail, item


def render(title: str, summary: str, items: Iterable[Any]) -> str:
    """Render navigation ``items`` as an ``llms.txt`` document.

    Args:
        title: Site name, used as the top-level heading.
        summary: One-line site description.
        items: Top-level MkDocs navigation items.

    Returns:
        The ``llms.txt`` text. Each top-level section becomes a heading, and
        each page a link to its Markdown source, labelled with the nested
        sections that lead to it.
    """
    lines = [f"# {title}", "", f"> {summary}", ""]
    lines += [
        "Every link is the Markdown source of one documentation page. Links",
        "inside those files are relative to the file that contains them.",
        "",
    ]
    for item in items:
        pages = list(_pages([item]))
        if not pages:
            continue
        lines += [f"## {item.title}", ""]
        for trail, page in pages:
            label = " / ".join((*trail[1:], str(page.title or page.file.src_uri)))
            lines.append(f"- [{label}]({page.file.src_uri})")
        lines.append("")
    return "\n".join(lines)


def on_nav(nav: Any, **_: Any) -> Any:
    """Keep the navigation so the page titles are available after the build."""
    _NAVIGATION["nav"] = nav
    return nav


def on_post_build(config: Any, **_: Any) -> None:
    """Write ``llms.txt`` and the Markdown source of every navigation page."""
    nav = _NAVIGATION["nav"]
    docs, site = Path(config["docs_dir"]), Path(config["site_dir"])
    for _trail, page in _pages(nav.items):
        target = site / page.file.src_uri
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(docs / page.file.src_uri, target)
    text = render(config["site_name"], config["site_description"], nav.items)
    (site / "llms.txt").write_text(text, encoding="utf-8")
