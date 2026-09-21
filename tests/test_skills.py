"""Pin the published skill and the user docs to the implemented interface.

Every ``canfar`` command, Python example, dotted API name, and link the skill
shows must be accepted by the CLI, the library, and the docs tree in this
checkout. The user docs get the same command and Python checks, so the skill
and the docs cannot drift from the code, or from each other, unnoticed.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import re
import shlex
import textwrap
import unicodedata
from pathlib import Path
from typing import Any, NamedTuple

import pytest
import typer
import yaml
from typer.testing import CliRunner

from canfar.cli.main import cli

ROOT = Path(__file__).parents[1]
SKILLS = ROOT / "skills"
DOCS = ROOT / "docs"

SKILL_FILES = sorted(SKILLS.rglob("*.md"))
# Contributor records, release notes, and the migration guide name removed
# interfaces on purpose; every other page describes the current interface.
DOC_FILES = sorted(
    path
    for path in DOCS.rglob("*.md")
    if path.relative_to(DOCS).parts[0] not in {"agents", "releases"}
    and path.relative_to(DOCS).as_posix() not in {"client/migration.md", "changelog.md"}
)
# Removed commands the user docs name while telling readers what replaced them.
# The skill gets no such allowance: it names only commands that exist.
REMOVED_COMMANDS = {("context",), ("storage",)}

DOCS_SITES = (
    "https://www.opencadc.org/canfar/",
    "https://opencadc.github.io/canfar/",
)
SHELL_LANGUAGES = {"bash", "sh", "shell", "zsh", "console"}
PYTHON_LANGUAGES = {"python", "py"}
SHELL_OPERATORS = {"|", "||", "&&", ";", ">", ">>", "<", "2>", "2>&1", "&"}

RUNNER = CliRunner()


class Block(NamedTuple):
    """One fenced code block."""

    language: str
    source: str


class Example(NamedTuple):
    """One checkable example and where it came from."""

    path: Path
    text: str

    @property
    def label(self) -> str:
        """Return a stable, readable parametrization ID."""
        summary = " ".join(self.text.split())[:60]
        return f"{self.path.relative_to(ROOT).as_posix()}::{summary}"


def _blocks(text: str) -> list[Block]:
    """Return fenced code blocks, including fences indented inside tabs."""
    blocks: list[Block] = []
    fence: str | None = None
    language = ""
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if fence is None:
            opened = re.match(r"(`{3,}|~{3,})\s*([\w+-]*)", stripped)
            if opened:
                fence, language, lines = opened.group(1), opened.group(2).lower(), []
        elif stripped.startswith(fence) and not stripped.strip(fence[0]):
            blocks.append(Block(language, textwrap.dedent("\n".join(lines))))
            fence = None
        else:
            lines.append(line)
    return blocks


def _prose(text: str) -> str:
    """Return the text outside fenced code blocks."""
    kept: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if fence is None:
            opened = re.match(r"(`{3,}|~{3,})", stripped)
            if opened:
                fence = opened.group(1)
            else:
                kept.append(line)
        elif stripped.startswith(fence) and not stripped.strip(fence[0]):
            fence = None
    return "\n".join(kept)


def _commands(text: str) -> list[str]:
    """Return every ``canfar`` command shown in shell blocks or inline code."""
    found: list[str] = []
    for block in _blocks(text):
        if block.language not in SHELL_LANGUAGES:
            continue
        joined = re.sub(r"\\\n\s*", " ", block.source)
        found += [
            line.strip().removeprefix("$ ")
            for line in joined.splitlines()
            if line.strip().removeprefix("$ ").startswith("canfar ")
        ]
    found += re.findall(r"`(canfar [^`\n]+)`", _prose(text))
    return found


def _argv(command: str) -> list[str] | None:
    """Return the CLI arguments of one shown command, or None for shorthand."""
    try:
        tokens = shlex.split(command, comments=True)[1:]
    except ValueError:
        return None
    for index, token in enumerate(tokens):
        if token in SHELL_OPERATORS:
            tokens = tokens[:index]
            break
    if "--" in tokens:
        tokens = tokens[: tokens.index("--")]
    # `canfar auth …` abbreviates a command family rather than showing a command.
    if any(token in {"…", "..."} for token in tokens):
        return None
    return tokens


def _examples(files: list[Path], extract: Any) -> list[Example]:
    return [
        Example(path, item)
        for path in files
        for item in dict.fromkeys(extract(path.read_text(encoding="utf-8")))
    ]


def _params(examples: list[Example]) -> list[Any]:
    return [pytest.param(example, id=example.label) for example in examples]


def _split_root(argv: list[str]) -> tuple[list[str], list[str]]:
    """Split leading root options, such as ``--log-file PATH``, from the command."""
    takes_value = {
        name: not (getattr(param, "is_flag", False) or getattr(param, "count", False))
        for param in typer.main.get_command(cli).params
        for name in getattr(param, "opts", [])
    }
    index = 0
    while index < len(argv) and argv[index].startswith("-") and argv[index] != "--":
        name = argv[index].split("=", 1)[0]
        index += 2 if takes_value.get(name) and "=" not in argv[index] else 1
    return argv[:index], argv[index:]


def _usage_error(argv: list[str]) -> str | None:
    """Return the usage error for arguments followed by an eager ``--help``."""
    result = RUNNER.invoke(cli, [*argv, "--help"])
    if result.exit_code == 0:
        return None
    lines = [line.strip(" │╭╰─╮╯") for line in result.output.splitlines()]
    return next(
        (line for line in lines if line.startswith(("No such", "Invalid", "Missing"))),
        f"exit code {result.exit_code}",
    )


def _rejection(command: str) -> str | None:
    """Return why the CLI rejects a shown command, or None when it parses.

    An eager ``--help`` stops parsing before anything runs, while an unknown
    command or option still fails with a usage error. Root options are checked
    apart from the command, because a root callback runs, and would configure
    logging or create a log file, before a leaf ``--help`` is reached.
    """
    argv = _argv(command)
    if argv is None:
        return None
    root, rest = _split_root(argv)
    return (_usage_error(root) if root else None) or _usage_error(rest)


# --- commands ---------------------------------------------------------------


@pytest.mark.parametrize("example", _params(_examples(SKILL_FILES, _commands)))
def test_skill_commands_exist(example: Example) -> None:
    """The skill names only commands and options the CLI accepts."""
    assert _rejection(example.text) is None, (
        f"`{example.text}` is not part of the CLI: {_rejection(example.text)}. "
        "State the command that exists instead."
    )


@pytest.mark.parametrize("example", _params(_examples(DOC_FILES, _commands)))
def test_doc_commands_exist(example: Example) -> None:
    """The user docs show only commands and options the CLI accepts."""
    argv = _argv(example.text) or []
    if tuple(argv[:1]) in REMOVED_COMMANDS:
        pytest.skip("named by the docs as a removed command")
    assert _rejection(example.text) is None, (
        f"`{example.text}` is not part of the CLI: {_rejection(example.text)}"
    )


def _output_owners() -> set[str]:
    """Return the command paths that own the ``-o/--output`` option."""
    owners: set[str] = set()

    def walk(command: Any, path: tuple[str, ...]) -> None:
        if any("--output" in getattr(p, "opts", []) for p in command.params):
            owners.add(" ".join(path))
        # `data` mounts an upstream application that owns its own stdout.
        if hasattr(command, "commands") and path != ("data",):
            for name, child in command.commands.items():
                walk(child, (*path, name))

    walk(typer.main.get_command(cli), ())
    return owners


def _listed(text: str, label: str) -> set[str]:
    """Return the backticked command names on the skill's labelled list line."""
    line = next(ln for ln in text.splitlines() if ln.startswith(f"- **{label}**"))
    return set(re.findall(r"`([a-z][a-z ]*)`", line.split(":", 1)[1]))


def test_skill_machine_output_list_matches_cli() -> None:
    """The skill's machine-output list is exactly the commands that own ``-o``."""
    text = (SKILLS / "canfar" / "SKILL.md").read_text(encoding="utf-8")
    owners = _output_owners()
    assert _listed(text, "Machine output") == owners
    assert not _listed(text, "Human text only") & owners


# --- Python -----------------------------------------------------------------


def _python(text: str) -> list[str]:
    return [b.source for b in _blocks(text) if b.language in PYTHON_LANGUAGES]


def _resolve(dotted: str) -> Any:
    """Import the longest module prefix of a dotted name, then walk attributes."""
    parts = dotted.split(".")
    for cut in range(len(parts), 0, -1):
        try:
            target: Any = importlib.import_module(".".join(parts[:cut]))
        except ImportError:
            continue
        for attribute in parts[cut:]:
            target = getattr(target, attribute)
        return target
    raise ImportError(dotted)


def _unknown_keywords(target: Any, call: ast.Call) -> list[str]:
    try:
        parameters = inspect.signature(target).parameters
    except (TypeError, ValueError):
        return []
    if any(p.kind is p.VAR_KEYWORD for p in parameters.values()):
        return []
    return [k.arg for k in call.keywords if k.arg and k.arg not in parameters]


def _imports(tree: ast.AST, problems: list[str]) -> dict[str, Any]:
    """Bind the names an example imports from ``canfar``, noting failures."""
    names: dict[str, Any] = {}
    for node in ast.walk(tree):
        wanted: dict[str, str] = {}
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "canfar"
        ):
            wanted = {a.asname or a.name: f"{node.module}.{a.name}" for a in node.names}
        elif isinstance(node, ast.Import):
            wanted = {
                a.asname or "canfar": a.name if a.asname else "canfar"
                for a in node.names
                if a.name.split(".")[0] == "canfar"
            }
        for name, dotted in wanted.items():
            try:
                names[name] = _resolve(dotted)
            except (ImportError, AttributeError):
                problems.append(f"cannot import {dotted}")
    return names


def _clients(tree: ast.AST, names: dict[str, Any]) -> dict[str, Any]:
    """Bind ``with Session() as s`` and ``s = Session()`` to their class."""
    clients: dict[str, Any] = {}
    for node in ast.walk(tree):
        pairs: list[tuple[ast.expr | None, ast.expr]] = []
        if isinstance(node, ast.With | ast.AsyncWith):
            pairs = [(item.optional_vars, item.context_expr) for item in node.items]
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            pairs = [(node.targets[0], node.value)]
        for variable, value in pairs:
            if (
                isinstance(variable, ast.Name)
                and isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and inspect.isclass(names.get(value.func.id))
            ):
                clients[variable.id] = names[value.func.id]
    return clients


def _python_problems(source: str) -> list[str]:
    """Return every way a Python example disagrees with the library."""
    flags = ast.PyCF_ONLY_AST | ast.PyCF_ALLOW_TOP_LEVEL_AWAIT
    try:
        tree = compile(source, "<example>", "exec", flags=flags)
    except SyntaxError:
        # Pages also show signatures, REPL transcripts, and elided fragments.
        return []
    problems: list[str] = []
    names = _imports(tree, problems)
    clients = _clients(tree, names)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in names:
            shown, target = func.id, names[func.id]
        elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            owner = clients.get(func.value.id, names.get(func.value.id))
            if owner is None:
                continue
            shown, target = (
                f"{func.value.id}.{func.attr}",
                getattr(owner, func.attr, None),
            )
            if target is None:
                problems.append(f"{shown} does not exist")
                continue
        else:
            continue
        problems += [
            f"{shown}() has no `{keyword}` argument"
            for keyword in _unknown_keywords(target, node)
        ]
    return problems


@pytest.mark.parametrize(
    "example", _params(_examples([*SKILL_FILES, *DOC_FILES], _python))
)
def test_python_examples_match_library(example: Example) -> None:
    """Python examples import real names and pass arguments the API accepts."""
    assert _python_problems(example.text) == []


def _dotted_names(text: str) -> list[str]:
    spans = re.findall(r"`([^`\n]+)`", _prose(text))
    return [
        f"canfar{match}"
        for span in spans
        for match in re.findall(r"(?<![\w.@/-])canfar((?:\.[A-Za-z_]\w*)+)", span)
    ]


@pytest.mark.parametrize("example", _params(_examples(SKILL_FILES, _dotted_names)))
def test_skill_api_names_resolve(example: Example) -> None:
    """Dotted API names in the skill's prose exist in the library."""
    _resolve(example.text)


# --- links and frontmatter --------------------------------------------------


def _slug(heading: str) -> str:
    """Slugify a heading the way the Markdown ``toc`` extension does."""
    text = re.sub(r"`|\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def _anchors(page: Path) -> set[str]:
    text = page.read_text(encoding="utf-8")
    explicit = re.findall(r'id="([^"]+)"', text) + re.findall(r"\{#([^}\s]+)", text)
    headings = re.findall(r"^#{1,6}\s+(.+?)\s*#*$", _prose(text), flags=re.MULTILINE)
    return {*explicit, *(_slug(heading) for heading in headings)}


def _doc_page(url: str) -> tuple[Path | None, str]:
    """Map a published docs URL to its source page and anchor."""
    site = next(base for base in DOCS_SITES if url.startswith(base))
    location, _, anchor = url.removeprefix(site).partition("#")
    parts = [part for part in location.split("/") if part]
    # `mike` publishes each version under an alias such as `latest`.
    if parts and not (DOCS / parts[0]).exists() and parts[0] != "index.md":
        parts = parts[1:]
    if not parts:
        return DOCS / "index.md", anchor
    stem = DOCS.joinpath(*parts)
    candidates = (stem.with_suffix(".md"), stem / "index.md")
    return next((page for page in candidates if page.is_file()), None), anchor


def _links(text: str) -> list[str]:
    inline = re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", text)
    bare = re.findall(r"(?<![(\w])(https?://[^\s)>`\]]+)", text)
    return [link.rstrip(".,;") for link in (*inline, *bare)]


@pytest.mark.parametrize("example", _params(_examples(SKILL_FILES, _links)))
def test_skill_links_resolve(example: Example) -> None:
    """The skill points only at docs pages, anchors, and files that exist."""
    link = example.text
    if link.startswith(DOCS_SITES) and link.endswith("/llms.txt"):
        # Written into the built site by the docs hook, not kept under docs/.
        assert "docs/hooks/llmstxt.py" in (ROOT / "mkdocs.yml").read_text()
    elif link.startswith(DOCS_SITES):
        page, anchor = _doc_page(link)
        assert page is not None, f"{link} has no page under docs/"
        assert not anchor or anchor in _anchors(page), f"{link}: no such anchor"
    elif not re.match(r"[a-z][a-z0-9+.-]*:", link):
        location, _, anchor = link.partition("#")
        target = example.path
        if location:
            target = (example.path.parent / location).resolve()
        assert target.is_file(), f"{link} does not exist"
        assert SKILLS in target.parents, f"{link} leaves the installed skill"
        assert not anchor or anchor in _anchors(target), f"{link}: no such anchor"


@pytest.mark.parametrize(
    "skill", sorted(SKILLS.glob("*/SKILL.md")), ids=lambda path: path.parent.name
)
def test_skill_frontmatter(skill: Path) -> None:
    """Frontmatter follows the Agent Skills format installers rely on."""
    text = skill.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    meta = yaml.safe_load(text.split("\n---\n", 1)[0].removeprefix("---\n"))
    assert meta["name"] == skill.parent.name
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", meta["name"])
    assert 0 < len(meta["description"]) <= 1024
