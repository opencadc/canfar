"""Tests for the AliasGroup class in canfar.hooks.typer.aliases."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from click.core import Command, Context
from typer.core import TyperGroup

from canfar.hooks.typer.aliases import AliasGroup


class TestAliasGroup:
    """Test cases for the AliasGroup class."""

    @pytest.fixture
    def alias_group(self) -> AliasGroup:
        """Create an AliasGroup instance for testing."""
        return AliasGroup()

    @pytest.fixture
    def mock_context(self) -> Context:
        """Create a mock Click context."""
        return Mock(spec=Context)

    @pytest.fixture
    def mock_command(self) -> Command:
        """Create a mock Click command."""
        return Mock(spec=Command)

    def test_alias_group_inherits_from_typer_group(
        self, alias_group: AliasGroup
    ) -> None:
        """Test that AliasGroup inherits from TyperGroup."""
        assert isinstance(alias_group, TyperGroup)

    def test_cmd_split_pattern_regex(self, alias_group: AliasGroup) -> None:
        """Test the regex pattern for splitting command names."""
        pattern = alias_group._CMD_SPLIT_P  # noqa: SLF001

        # Test comma separation
        assert pattern.split("cmd1,cmd2") == ["cmd1", "cmd2"]
        assert pattern.split("cmd1, cmd2") == ["cmd1", "cmd2"]
        assert pattern.split("cmd1 ,cmd2") == ["cmd1", "cmd2"]
        assert pattern.split("cmd1 , cmd2") == ["cmd1", "cmd2"]

        # Test pipe separation
        assert pattern.split("cmd1|cmd2") == ["cmd1", "cmd2"]
        assert pattern.split("cmd1| cmd2") == ["cmd1", "cmd2"]
        assert pattern.split("cmd1 |cmd2") == ["cmd1", "cmd2"]
        assert pattern.split("cmd1 | cmd2") == ["cmd1", "cmd2"]

        # Test mixed separators
        assert pattern.split("cmd1,cmd2|cmd3") == ["cmd1", "cmd2", "cmd3"]

        # Test single command (no split)
        assert pattern.split("single") == ["single"]

    def test_group_cmd_name_with_exact_match(self, alias_group: AliasGroup) -> None:
        """Test _group_cmd_name when the default matches exactly."""
        mock_cmd = Mock()
        mock_cmd.name = "show"
        alias_group.commands = {"show": mock_cmd}

        result = alias_group._group_cmd_name("show")  # noqa: SLF001
        assert result == "show"

    def test_group_cmd_name_with_alias_match(self, alias_group: AliasGroup) -> None:
        """Test _group_cmd_name when the default matches an alias."""
        mock_cmd = Mock()
        mock_cmd.name = "show | list | ls"
        alias_group.commands = {"show": mock_cmd}

        # Test each alias
        assert alias_group._group_cmd_name("show") == "show | list | ls"  # noqa: SLF001
        assert alias_group._group_cmd_name("list") == "show | list | ls"  # noqa: SLF001
        assert alias_group._group_cmd_name("ls") == "show | list | ls"  # noqa: SLF001

    def test_group_cmd_name_with_no_match(self, alias_group: AliasGroup) -> None:
        """Test _group_cmd_name when no command matches."""
        mock_cmd = Mock()
        mock_cmd.name = "show | list"
        alias_group.commands = {"show": mock_cmd}

        result = alias_group._group_cmd_name("nonexistent")  # noqa: SLF001
        assert result == "nonexistent"

    def test_group_cmd_name_with_empty_commands(self, alias_group: AliasGroup) -> None:
        """Test _group_cmd_name with empty commands dict."""
        alias_group.commands = {}

        result = alias_group._group_cmd_name("anything")  # noqa: SLF001
        assert result == "anything"

    def test_group_cmd_name_with_command_without_name(
        self, alias_group: AliasGroup
    ) -> None:
        """Test _group_cmd_name with command that has no name attribute."""
        mock_cmd = Mock()
        del mock_cmd.name  # Remove the name attribute
        alias_group.commands = {"test": mock_cmd}

        result = alias_group._group_cmd_name("test")  # noqa: SLF001
        assert result == "test"

    def test_group_cmd_name_with_empty_name(self, alias_group: AliasGroup) -> None:
        """Test _group_cmd_name with command that has empty name."""
        mock_cmd = Mock()
        mock_cmd.name = ""
        alias_group.commands = {"test": mock_cmd}

        result = alias_group._group_cmd_name("test")  # noqa: SLF001
        assert result == "test"

    def test_get_command_calls_group_cmd_name(
        self, alias_group: AliasGroup, mock_context: Context
    ) -> None:
        """Test that get_command calls _group_cmd_name and super().get_command."""
        mock_cmd = Mock()
        mock_cmd.name = "show | list"
        alias_group.commands = {"show": mock_cmd}

        # Mock the parent class method
        with patch.object(
            alias_group.__class__.__bases__[0], "get_command"
        ) as mock_super:
            mock_super.return_value = mock_cmd

            result = alias_group.get_command(mock_context, "list")

            # Verify that super().get_command was called with the resolved name
            mock_super.assert_called_once_with(mock_context, "show | list")
            assert result == mock_cmd

    def test_get_command_with_nonexistent_alias(
        self, alias_group: AliasGroup, mock_context: Context
    ) -> None:
        """Test get_command with a non-existent command/alias."""
        alias_group.commands = {}

        with patch.object(
            alias_group.__class__.__bases__[0], "get_command"
        ) as mock_super:
            mock_super.return_value = None

            result = alias_group.get_command(mock_context, "nonexistent")

            mock_super.assert_called_once_with(mock_context, "nonexistent")
            assert result is None

    def test_get_command_integration(
        self, alias_group: AliasGroup, mock_context: Context
    ) -> None:
        """Integration test for get_command with real command setup."""
        # Create a mock command with aliases
        mock_cmd = Mock(spec=Command)
        mock_cmd.name = "show | list | ls"
        alias_group.commands = {"show": mock_cmd}

        with patch.object(
            alias_group.__class__.__bases__[0], "get_command"
        ) as mock_super:
            mock_super.return_value = mock_cmd

            # Test that all aliases resolve to the same command
            for alias in ["show", "list", "ls"]:
                result = alias_group.get_command(mock_context, alias)
                assert result == mock_cmd

            # Verify super was called with the full command name each time
            assert mock_super.call_count == 3
            for call in mock_super.call_args_list:
                assert (
                    call[0][1] == "show | list | ls"
                )  # Second argument should be the resolved name

    def test_multiple_commands_with_aliases(self, alias_group: AliasGroup) -> None:
        """Test _group_cmd_name with multiple commands having different aliases."""
        cmd1 = Mock()
        cmd1.name = "show | list | ls"
        cmd2 = Mock()
        cmd2.name = "create | new | add"
        cmd3 = Mock()
        cmd3.name = "delete"

        alias_group.commands = {
            "show": cmd1,
            "create": cmd2,
            "delete": cmd3,
        }

        # Test first command aliases
        assert alias_group._group_cmd_name("show") == "show | list | ls"  # noqa: SLF001
        assert alias_group._group_cmd_name("list") == "show | list | ls"  # noqa: SLF001
        assert alias_group._group_cmd_name("ls") == "show | list | ls"  # noqa: SLF001

        # Test second command aliases
        assert alias_group._group_cmd_name("create") == "create | new | add"  # noqa: SLF001
        assert alias_group._group_cmd_name("new") == "create | new | add"  # noqa: SLF001
        assert alias_group._group_cmd_name("add") == "create | new | add"  # noqa: SLF001

        # Test third command (no aliases)
        assert alias_group._group_cmd_name("delete") == "delete"  # noqa: SLF001

        # Test non-existent command
        assert alias_group._group_cmd_name("nonexistent") == "nonexistent"  # noqa: SLF001
