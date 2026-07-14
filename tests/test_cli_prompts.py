"""Public behavior for interactive CLI selection prompts."""

from unittest.mock import MagicMock, patch

from pydantic import AnyHttpUrl, AnyUrl

from canfar.cli.prompts import select_server
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


def test_select_server_keeps_questionary_choice_output() -> None:
    """Multiple servers remain an interactive CLI choice with stable labels."""
    first = _server("Alpha", "ivo://alpha.example/skaha")
    second = _server("Beta", "ivo://beta.example/skaha")
    prompt = MagicMock()
    prompt.ask.return_value = second

    with patch(
        "canfar.cli.prompts.questionary.select",
        return_value=prompt,
    ) as choose:
        selected = select_server([first, second])

    assert selected is second
    assert choose.call_args.args == ("Select a Science Platform Server",)
    choices = choose.call_args.kwargs["choices"]
    assert [choice.title for choice in choices] == [
        "Alpha (ivo://alpha.example/skaha)",
        "Beta (ivo://beta.example/skaha)",
    ]
    assert [choice.value for choice in choices] == [first, second]
    assert choose.call_args.kwargs["style"] is not None
