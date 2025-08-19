"""Comprehensive tests for the display.capabilities function."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import questionary

from canfar.utils.display import (
    _configure_auth_choices,
    _configure_version_choices,
    _get_selection_style,
    capabilities,
)


class TestDisplayCapabilities:
    """Test cases for the display.capabilities function."""

    @pytest.fixture
    def sample_capabilities(self) -> list[dict[str, Any]]:
        """Provide sample capabilities data for testing."""
        return [
            {
                "baseurl": "https://rc-uv.canfar.net/skaha",
                "version": "v0",
                "auth_modes": ["x509", "oidc", "cookie"],
            },
            {
                "baseurl": "https://rc-uv.canfar.net/skaha",
                "version": "v1",
                "auth_modes": ["x509", "oidc", "cookie"],
            },
        ]

    @pytest.fixture
    def single_capability(self) -> list[dict[str, Any]]:
        """Provide single capability for testing."""
        return [
            {
                "baseurl": "https://test.canfar.net/skaha",
                "version": "v2",
                "auth_modes": ["oidc"],
            }
        ]

    @pytest.fixture
    def capability_no_auth(self) -> list[dict[str, Any]]:
        """Provide capability with no auth modes."""
        return [
            {
                "baseurl": "https://bad.canfar.net/skaha",
                "version": "v1",
                "auth_modes": [],
            }
        ]

    @pytest.mark.asyncio
    async def test_capabilities_empty_list(self) -> None:
        """Test capabilities function with empty list."""
        with pytest.raises(SystemExit) as exc_info:
            await capabilities([])
        assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_capabilities_no_auth_modes(
        self, capability_no_auth: list[dict[str, Any]]
    ) -> None:
        """Test capabilities function when selected version has no auth modes."""
        # Mock the version selection to return the capability with no auth modes
        with patch("canfar.utils.display.questionary.select") as mock_select:
            mock_select.return_value.ask_async = AsyncMock(
                return_value=capability_no_auth[0]
            )

            with pytest.raises(SystemExit) as exc_info:
                await capabilities(capability_no_auth)
            assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_capabilities_keyboard_interrupt_version(
        self, sample_capabilities: list[dict[str, Any]]
    ) -> None:
        """Handle KeyboardInterrupt during version selection."""
        with patch("canfar.utils.display.questionary.select") as mock_select:
            mock_select.return_value.ask_async = AsyncMock(
                side_effect=KeyboardInterrupt
            )

            with pytest.raises(SystemExit) as exc_info:
                await capabilities(sample_capabilities)
            assert exc_info.value.code == 0

    @pytest.mark.asyncio
    async def test_capabilities_user_cancel_version(
        self, sample_capabilities: list[dict[str, Any]]
    ) -> None:
        """Handle user cancellation during version selection."""
        with patch("canfar.utils.display.questionary.select") as mock_select:
            mock_select.return_value.ask_async = AsyncMock(return_value=None)

            with pytest.raises(SystemExit) as exc_info:
                await capabilities(sample_capabilities)
            assert exc_info.value.code == 0

    @pytest.mark.asyncio
    async def test_capabilities_keyboard_interrupt_auth(
        self, sample_capabilities: list[dict[str, Any]]
    ) -> None:
        """Handle KeyboardInterrupt during auth selection."""
        with patch("canfar.utils.display.questionary.select") as mock_select:
            # First call (version selection) returns valid capability
            # Second call (auth selection) raises KeyboardInterrupt
            mock_select.return_value.ask_async = AsyncMock(
                side_effect=[sample_capabilities[0], KeyboardInterrupt()]
            )

            with pytest.raises(SystemExit) as exc_info:
                await capabilities(sample_capabilities)
            assert exc_info.value.code == 0

    @pytest.mark.asyncio
    async def test_capabilities_user_cancel_auth(
        self, sample_capabilities: list[dict[str, Any]]
    ) -> None:
        """Handle user cancellation during auth selection."""
        with patch("canfar.utils.display.questionary.select") as mock_select:
            # First call (version selection) returns valid capability
            # Second call (auth selection) returns None (user cancel)
            mock_select.return_value.ask_async = AsyncMock(
                side_effect=[sample_capabilities[0], None]
            )

            with pytest.raises(SystemExit) as exc_info:
                await capabilities(sample_capabilities)
            assert exc_info.value.code == 0

    @pytest.mark.asyncio
    async def test_capabilities_successful_selection(
        self, sample_capabilities: list[dict[str, Any]]
    ) -> None:
        """Test successful capability selection workflow."""
        with patch("canfar.utils.display.questionary.select") as mock_select:
            # Mock version selection to return v1 capability
            # Mock auth selection to return 'oidc'
            mock_select.return_value.ask_async = AsyncMock(
                side_effect=[sample_capabilities[1], "oidc"]
            )

            version, auth = await capabilities(sample_capabilities)
            assert version == "v1"
            assert auth == "oidc"

    @pytest.mark.asyncio
    async def test_capabilities_single_option(
        self, single_capability: list[dict[str, Any]]
    ) -> None:
        """Test capabilities with single version and auth option."""
        with patch("canfar.utils.display.questionary.select") as mock_select:
            # Mock selections
            mock_select.return_value.ask_async = AsyncMock(
                side_effect=[single_capability[0], "oidc"]
            )

            version, auth = await capabilities(single_capability)
            assert version == "v2"
            assert auth == "oidc"

    @pytest.mark.asyncio
    async def test_capabilities_missing_version_key(self) -> None:
        """Test capabilities with missing version key."""
        caps_no_version = [
            {
                "baseurl": "https://test.canfar.net/skaha",
                "auth_modes": ["x509"],
            }
        ]

        with patch("canfar.utils.display.questionary.select") as mock_select:
            mock_select.return_value.ask_async = AsyncMock(
                side_effect=[caps_no_version[0], "x509"]
            )

            version, auth = await capabilities(caps_no_version)
            assert version == ""  # Should default to empty string
            assert auth == "x509"

    def test_configure_version_choices_empty(self) -> None:
        """Test _configure_version_choices with empty capabilities."""
        choices = _configure_version_choices([])
        assert choices == []

    def test_configure_version_choices_valid(
        self, sample_capabilities: list[dict[str, Any]]
    ) -> None:
        """Test _configure_version_choices with valid capabilities."""
        choices = _configure_version_choices(sample_capabilities)

        assert len(choices) == 2
        assert all(isinstance(choice, questionary.Choice) for choice in choices)

        # Check that choices contain expected information
        choice_titles = [choice.title for choice in choices]
        assert any("v0" in title for title in choice_titles)
        assert any("v1" in title for title in choice_titles)
        assert all("rc-uv.canfar.net" in title for title in choice_titles)

    def test_configure_version_choices_formatting(self) -> None:
        """Test _configure_version_choices formatting with different lengths."""
        caps = [
            {
                "baseurl": "https://short.net/api",
                "version": "v1",
                "auth_modes": ["x509"],
            },
            {
                "baseurl": "https://very-long-domain-name.net/api",
                "version": "v10",
                "auth_modes": ["oidc", "cookie"],
            },
        ]

        choices = _configure_version_choices(caps)
        assert len(choices) == 2

        # Check that formatting includes emoji and brackets
        for choice in choices:
            assert "🔧" in choice.title
            assert "[" in choice.title
            assert "]" in choice.title

    def test_configure_auth_choices_empty(self) -> None:
        """Test _configure_auth_choices with empty auth modes."""
        choices = _configure_auth_choices([])
        assert choices == []

    def test_configure_auth_choices_unknown_mode(self) -> None:
        """Test _configure_auth_choices with unknown auth mode."""
        auth_modes = ["unknown_auth"]
        choices = _configure_auth_choices(auth_modes)

        assert len(choices) == 1
        assert "UNKNOWN_AUTH Authentication" in choices[0].title
        assert choices[0].value == "unknown_auth"

    def test_configure_auth_choices_formatting(self) -> None:
        """Test _configure_auth_choices formatting."""
        auth_modes = ["x509", "oidc"]
        choices = _configure_auth_choices(auth_modes)

        # Check that all choices have consistent formatting
        for choice in choices:
            assert "🔐" in choice.title
            assert " - " in choice.title

    def test_get_selection_style(self) -> None:
        """Test _get_selection_style returns valid questionary style."""
        style = _get_selection_style()

        assert isinstance(style, questionary.Style)
        # Check that it's a valid style object by ensuring it can be used
        # The Style object doesn't expose its internal structure, so we just verify type
        assert style is not None


class TestDisplayCapabilitiesIntegration:
    """Integration tests for display capabilities function."""

    @pytest.fixture
    def complex_capabilities(self) -> list[dict[str, Any]]:
        """Provide complex capabilities data for integration testing."""
        return [
            {
                "baseurl": "https://dev.canfar.net/skaha",
                "version": "v0",
                "auth_modes": ["cookie"],
            },
            {
                "baseurl": "https://staging.canfar.net/skaha",
                "version": "v1",
                "auth_modes": ["x509", "oidc"],
            },
            {
                "baseurl": "https://prod.canfar.net/skaha",
                "version": "v2",
                "auth_modes": ["oidc"],
            },
        ]

    @pytest.mark.asyncio
    async def test_capabilities_multiple_versions(
        self, complex_capabilities: list[dict[str, Any]]
    ) -> None:
        """Select among multiple versions with different auth modes."""
        with patch("canfar.utils.display.questionary.select") as mock_select:
            # Select v1 (staging) and x509 auth
            mock_select.return_value.ask_async = AsyncMock(
                side_effect=[complex_capabilities[1], "x509"]
            )

            version, auth = await capabilities(complex_capabilities)
            assert version == "v1"
            assert auth == "x509"

    @pytest.mark.asyncio
    async def test_capabilities_calls_questionary_twice(
        self, complex_capabilities: list[dict[str, Any]]
    ) -> None:
        """Ensure questionary.select is called twice (version, then auth)."""
        with patch("canfar.utils.display.questionary.select") as mock_select:
            mock_select.return_value.ask_async = AsyncMock(
                side_effect=[complex_capabilities[2], "oidc"]
            )

            await capabilities(complex_capabilities)

            # Should be called twice: once for version, once for auth
            assert mock_select.call_count == 2

    @pytest.mark.asyncio
    async def test_capabilities_console_output_empty(self) -> None:
        """Print error when capabilities are empty."""
        with patch("canfar.utils.display.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            with pytest.raises(SystemExit):
                await capabilities([])

            # Check that console.print was called with error message
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "No server capabilities available" in call_args

    @pytest.mark.asyncio
    async def test_capabilities_console_output_no_auth(self) -> None:
        """Test console output when selected version has no auth modes."""
        caps_no_auth = [
            {"baseurl": "https://test.net", "version": "v1", "auth_modes": []}
        ]

        with (
            patch("canfar.utils.display.Console") as mock_console_class,
            patch("canfar.utils.display.questionary.select") as mock_select,
        ):
            mock_console = Mock()
            mock_console_class.return_value = mock_console
            mock_select.return_value.ask_async = AsyncMock(return_value=caps_no_auth[0])

            with pytest.raises(SystemExit):
                await capabilities(caps_no_auth)

            # Should print error about no auth modes
            mock_console.print.assert_called()
            call_args = str(mock_console.print.call_args)
            assert "authentication modes available" in call_args.lower()
