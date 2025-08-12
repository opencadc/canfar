"""Tests for utility modules."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import questionary

from canfar.models.registry import Server, ServerResults
from canfar.utils.convert import dict_to_tuples
from canfar.utils.display import configure_server_choices, servers


# Tests for convert module
def test_dict_to_tuples_empty() -> None:
    assert dict_to_tuples({}) == []


def test_dict_to_tuples_simple() -> None:
    assert dict_to_tuples({"a": 1, "b": 2}) == [("a", 1), ("b", 2)]


def test_dict_to_tuples_nested() -> None:
    assert dict_to_tuples({"a": {"x": 1, "y": 2}, "b": 3}) == [
        ("a", "x=1"),
        ("a", "y=2"),
        ("b", 3),
    ]


def test_dict_to_tuples_mixed() -> None:
    assert dict_to_tuples({"a": 1, "b": {"x": 2}, "c": {"y": 3, "z": 4}}) == [
        ("a", 1),
        ("b", "x=2"),
        ("c", "y=3"),
        ("c", "z=4"),
    ]


def test_dict_to_tuples_non_string_keys() -> None:
    assert dict_to_tuples({1: "a", 2: {"x": "b"}}) == [(1, "a"), (2, "x=b")]


# Tests for display module
def create_test_server(
    registry: str = "TestRegistry",
    uri: str = "ivo://test.org/skaha",
    url: str = "https://test.example.com/skaha",
    status: int | None = 200,
    name: str | None = "Test Server",
) -> Server:
    """Create a test Server instance.

    Args:
        registry: Registry name
        uri: Server URI
        url: Server URL
        status: HTTP status code (None for dead servers)
        name: Server name

    Returns:
        Server: Test server instance
    """
    return Server(
        registry=registry,
        uri=uri,
        url=url,
        status=status,
        name=name,
    )


def create_test_results(endpoints: list[Server]) -> ServerResults:
    """Create test ServerResults instance.

    Args:
        endpoints: List of server endpoints

    Returns:
        ServerResults: Test results instance
    """
    results = ServerResults()
    for endpoint in endpoints:
        results.add(endpoint)
    return results


def test_configure_server_choices_alive_only() -> None:
    """Test configure_server_choices with only alive servers."""
    alive = [
        create_test_server("Registry1", name="Server1"),
        create_test_server("Registry2", name="Server2"),
    ]
    dead = []

    choices = configure_server_choices(
        show_dead=False, show_details=False, alive=alive, dead=dead
    )

    assert len(choices) == 2
    assert all(isinstance(choice, questionary.Choice) for choice in choices)
    assert "🟢" in choices[0].title
    assert "Server1" in choices[0].title
    assert "Registry1" in choices[0].title
    assert choices[0].value == alive[0]


def test_configure_server_choices_with_dead() -> None:
    """Test configure_server_choices including dead servers."""
    alive = [create_test_server("Registry1", name="Server1")]
    dead = [create_test_server("Registry2", name="Server2", status=None)]

    choices = configure_server_choices(
        show_dead=True, show_details=False, alive=alive, dead=dead
    )

    assert len(choices) == 2
    assert "🟢" in choices[0].title  # alive server
    assert "🔴" in choices[1].title  # dead server


def test_configure_server_choices_with_details() -> None:
    """Test configure_server_choices with detailed information."""
    alive = [
        create_test_server(
            "Registry1",
            uri="ivo://test1.org/skaha",
            url="https://test1.example.com/skaha",
            name="Server1",
        )
    ]
    dead = []

    choices = configure_server_choices(
        show_dead=False, show_details=True, alive=alive, dead=dead
    )

    assert len(choices) == 1
    choice_title = choices[0].title
    assert "ivo://test1.org/skaha" in choice_title
    assert "https://test1.example.com/skaha" in choice_title


def test_configure_server_choices_unknown_name() -> None:
    """Test configure_server_choices with server having no name."""
    alive = [create_test_server("Registry1", name=None)]
    dead = []

    choices = configure_server_choices(
        show_dead=False, show_details=False, alive=alive, dead=dead
    )

    assert len(choices) == 1
    assert "Unknown" in choices[0].title


def test_configure_server_choices_empty() -> None:
    """Test configure_server_choices with no servers."""
    choices = configure_server_choices(
        show_dead=False, show_details=False, alive=[], dead=[]
    )

    assert len(choices) == 0


@pytest.mark.asyncio
async def test_servers_successful_selection() -> None:
    """Test servers function with successful server selection."""
    test_server = create_test_server("TestRegistry", name="TestServer")
    results = create_test_results([test_server])

    with patch("questionary.select") as mock_select:
        mock_question = AsyncMock()
        mock_question.ask_async.return_value = test_server
        mock_select.return_value = mock_question

        result = await servers(results)

        assert result == test_server
        mock_select.assert_called_once()


@pytest.mark.asyncio
async def test_servers_keyboard_interrupt() -> None:
    """Test servers function handling KeyboardInterrupt."""
    test_server = create_test_server("TestRegistry", name="TestServer")
    results = create_test_results([test_server])

    with patch("questionary.select") as mock_select:
        mock_question = AsyncMock()
        mock_question.ask_async.side_effect = KeyboardInterrupt()
        mock_select.return_value = mock_question

        with patch("sys.exit") as mock_exit:
            await servers(results)
            mock_exit.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_servers_user_cancellation() -> None:
    """Test servers function when user cancels selection."""
    test_server = create_test_server("TestRegistry", name="TestServer")
    results = create_test_results([test_server])

    with patch("questionary.select") as mock_select:
        mock_question = AsyncMock()
        mock_question.ask_async.return_value = None  # User cancelled
        mock_select.return_value = mock_question

        with patch("sys.exit") as mock_exit:
            await servers(results)
            mock_exit.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_servers_with_show_dead_true() -> None:
    """Test servers function with show_dead=True."""
    alive_server = create_test_server("Registry1", name="AliveServer", status=200)
    dead_server = create_test_server("Registry2", name="DeadServer", status=None)
    results = create_test_results([alive_server, dead_server])

    with patch("questionary.select") as mock_select:
        mock_question = AsyncMock()
        mock_question.ask_async.return_value = alive_server
        mock_select.return_value = mock_question

        result = await servers(results, show_dead=True)

        assert result == alive_server
        # Verify that configure_server_choices was called with show_dead=True
        mock_select.assert_called_once()
        call_args = mock_select.call_args
        assert "choices" in call_args.kwargs
        # Should have 2 choices (alive + dead)
        assert len(call_args.kwargs["choices"]) == 2


@pytest.mark.asyncio
async def test_servers_with_show_details_true() -> None:
    """Test servers function with show_details=True."""
    test_server = create_test_server(
        "TestRegistry",
        uri="ivo://test.org/skaha",
        url="https://test.example.com/skaha",
        name="TestServer",
    )
    results = create_test_results([test_server])

    with patch("questionary.select") as mock_select:
        mock_question = AsyncMock()
        mock_question.ask_async.return_value = test_server
        mock_select.return_value = mock_question

        result = await servers(results, show_details=True)

        assert result == test_server
        mock_select.assert_called_once()
        call_args = mock_select.call_args
        # Verify that the choice includes detailed information
        choice_title = call_args.kwargs["choices"][0].title
        assert "ivo://test.org/skaha" in choice_title
        assert "https://test.example.com/skaha" in choice_title


@pytest.mark.asyncio
async def test_servers_mixed_status() -> None:
    """Test servers function with mixed alive and dead servers."""
    alive1 = create_test_server("Registry1", name="Alive1", status=200)
    alive2 = create_test_server("Registry2", name="Alive2", status=200)
    dead1 = create_test_server("Registry3", name="Dead1", status=None)
    dead2 = create_test_server("Registry4", name="Dead2", status=500)

    results = create_test_results([alive1, alive2, dead1, dead2])

    with patch("questionary.select") as mock_select:
        mock_question = AsyncMock()
        mock_question.ask_async.return_value = alive1
        mock_select.return_value = mock_question

        result = await servers(results, show_dead=False)

        assert result == alive1
        mock_select.assert_called_once()
        call_args = mock_select.call_args
        # Should only show alive servers (2 choices)
        assert len(call_args.kwargs["choices"]) == 2
