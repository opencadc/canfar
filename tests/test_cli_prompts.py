"""Public behavior for interactive CLI selection prompts."""

import pytest
from pydantic import AnyHttpUrl, AnyUrl
from rich.text import Text

from canfar.cli.prompts import select_idp, select_server
from canfar.idp import list_idps
from canfar.models.http import Server


def _server(name: str, uri: str) -> Server:
    return Server(
        idp="srcnet",
        name=name,
        uri=AnyUrl(uri),
        url=AnyHttpUrl(f"https://{name.casefold()}.example/skaha"),
        version="v1",
        auths=["oidc"],
    )


def test_select_server_lists_numbered_choices(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Multiple servers become numbered choices with stable labels."""
    first = _server("Alpha", "ivo://alpha.example/skaha")
    second = _server("Beta", "ivo://beta.example/skaha")
    answers = iter(["3", "2"])
    monkeypatch.setattr("builtins.input", lambda *_args: next(answers))

    selected = select_server([first, second])

    assert selected is second
    lines = Text.from_ansi(capsys.readouterr().out).plain.splitlines()
    assert lines[:3] == [
        "Select a Science Platform Server",
        "  1. Alpha (ivo://alpha.example/skaha)",
        "  2. Beta (ivo://beta.example/skaha)",
    ]
    assert "Please select one of the available options" in "\n".join(lines)


def test_select_server_returns_the_only_server_without_prompting() -> None:
    """One server needs no choice."""
    only = _server("Alpha", "ivo://alpha.example/skaha")

    assert select_server([only]) is only


def test_select_idp_returns_the_chosen_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """The chosen number maps to the IDP's canonical key."""
    idps = list_idps()
    monkeypatch.setattr("builtins.input", lambda *_args: str(len(idps)))

    assert select_idp(idps) == idps[-1].key


def test_cancelled_selection_exits_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    """End of input cancels the prompt with a zero exit status."""

    def cancel(*_args: object) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", cancel)

    with pytest.raises(SystemExit) as exit_info:
        select_idp(list_idps())

    assert exit_info.value.code == 0
