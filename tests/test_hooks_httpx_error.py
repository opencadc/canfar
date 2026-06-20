"""Tests for httpx error hooks."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from canfar.hooks.httpx.errors import acatch, catch


class TestCatch:
    """Test the catch function."""

    def test_catch_successful_response(self) -> None:
        """Test catch with successful response."""
        # Create mock response that doesn't raise an error
        mock_response = Mock(spec=httpx.Response)
        mock_response.read.return_value = b"success"
        mock_response.raise_for_status.return_value = None

        # Should not raise any exception
        catch(mock_response)

        # Verify response.read() was called
        mock_response.read.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    def test_catch_http_error_response(self) -> None:
        """Test catch with HTTP error response."""
        # Create mock response that raises HTTPError
        mock_response = Mock(spec=httpx.Response)
        mock_response.read.return_value = b"error content"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Client error", request=Mock(), response=mock_response
        )
        mock_response.status_code = 404
        mock_response.reason_phrase = "Not Found"
        mock_response.text = "Not Found"

        with pytest.raises(httpx.HTTPStatusError):
            catch(mock_response)

        # Verify response.read() was called
        mock_response.read.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    def test_catch_redacts_bearer_token_in_error_body(self) -> None:
        """HTTP status logs redact bearer tokens from response bodies."""
        request = httpx.Request("GET", "https://example.com/skaha/v1/context")
        response = httpx.Response(
            401,
            request=request,
            text="unhandled auth: Authorization Bearer abc.def.ghi",
        )

        with (
            patch("canfar.hooks.httpx.errors.log") as log,
            pytest.raises(httpx.HTTPStatusError),
        ):
            catch(response)

        error_text = " ".join(str(arg) for arg in log.warning.call_args.args)
        assert "abc.def.ghi" not in error_text
        assert "Authorization Bearer <redacted>" in error_text
        assert log.warning.call_args.kwargs["exc_info"] is False

    def test_catch_other_http_error(self) -> None:
        """Test catch with other HTTPError types."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.read.return_value = b"error content"
        mock_response.raise_for_status.side_effect = httpx.RequestError("Network error")
        mock_response.status_code = 500
        mock_response.reason_phrase = "Internal Server Error"
        mock_response.text = "Server Error"

        with pytest.raises(httpx.RequestError):
            catch(mock_response)

        # Verify response.read() was called
        mock_response.read.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    def test_catch_read_raises_propagates_without_warning_log(self) -> None:
        """Pin behavior: ReadTimeout from response.read() propagates unlogged.

        The refactored ``catch`` calls ``response.read()`` before the shared
        try/except ladder, so a body-download ``ReadTimeout`` is not
        warning-logged by the hook — it propagates directly to the caller.
        """
        mock_response = Mock(spec=httpx.Response)
        mock_response.read.side_effect = httpx.ReadTimeout("body download timed out")

        with (
            patch("canfar.hooks.httpx.errors.log") as mock_log,
            pytest.raises(httpx.ReadTimeout),
        ):
            catch(mock_response)

        mock_log.warning.assert_not_called()
        mock_response.raise_for_status.assert_not_called()


class TestACatch:
    """Test the acatch function."""

    @pytest.mark.asyncio
    async def test_acatch_successful_response(self) -> None:
        """Test acatch with successful response."""
        # Create mock response that doesn't raise an error
        mock_response = Mock(spec=httpx.Response)
        mock_response.aread = AsyncMock(return_value=b"success")
        mock_response.raise_for_status.return_value = None

        # Should not raise any exception
        await acatch(mock_response)

        # Verify response.aread() was called
        mock_response.aread.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_acatch_http_error_response(self) -> None:
        """Test acatch with HTTP error response."""
        # Create mock response that raises HTTPError
        mock_response = Mock(spec=httpx.Response)
        mock_response.aread = AsyncMock(return_value=b"error content")
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Client error", request=Mock(), response=mock_response
        )
        mock_response.status_code = 401
        mock_response.reason_phrase = "Unauthorized"
        mock_response.text = "Unauthorized"

        with pytest.raises(httpx.HTTPStatusError):
            await acatch(mock_response)

        # Verify response.aread() was called
        mock_response.aread.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_acatch_other_http_error(self) -> None:
        """Test acatch with other HTTPError types."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.aread = AsyncMock(return_value=b"error content")
        mock_response.raise_for_status.side_effect = httpx.RequestError("Network error")
        mock_response.status_code = 503
        mock_response.reason_phrase = "Service Unavailable"
        mock_response.text = "Service Unavailable"

        with pytest.raises(httpx.RequestError):
            await acatch(mock_response)

        # Verify response.aread() was called
        mock_response.aread.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_acatch_timeout_error(self) -> None:
        """Test acatch with timeout error."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.aread = AsyncMock(return_value=b"")
        mock_response.raise_for_status.side_effect = httpx.TimeoutException(
            "Request timeout"
        )
        mock_response.status_code = 408
        mock_response.reason_phrase = "Request Timeout"
        mock_response.text = "Request Timeout"

        with pytest.raises(httpx.TimeoutException):
            await acatch(mock_response)

        # Verify response.aread() was called
        mock_response.aread.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_acatch_redacts_bearer_token_in_error_body(self) -> None:
        """Async HTTP status logs redact bearer tokens from response bodies."""
        request = httpx.Request("GET", "https://example.com/skaha/v1/context")
        response = httpx.Response(
            401,
            request=request,
            text="unhandled auth: Authorization Bearer abc.def.ghi",
        )

        with (
            patch("canfar.hooks.httpx.errors.log") as log,
            pytest.raises(httpx.HTTPStatusError),
        ):
            await acatch(response)

        error_text = " ".join(str(arg) for arg in log.warning.call_args.args)
        assert "abc.def.ghi" not in error_text
        assert "Authorization Bearer <redacted>" in error_text
        assert log.warning.call_args.kwargs["exc_info"] is False

    @pytest.mark.asyncio
    async def test_acatch_aread_raises_propagates_without_warning_log(self) -> None:
        """Pin behavior: ReadTimeout from aread() propagates unlogged.

        The refactored ``acatch`` calls ``await response.aread()`` before the shared
        try/except ladder, so a body-download ``ReadTimeout`` is not
        warning-logged by the hook — it propagates directly to the caller.
        """
        mock_response = Mock(spec=httpx.Response)
        mock_response.aread = AsyncMock(
            side_effect=httpx.ReadTimeout("body download timed out")
        )

        with (
            patch("canfar.hooks.httpx.errors.log") as mock_log,
            pytest.raises(httpx.ReadTimeout),
        ):
            await acatch(mock_response)

        mock_log.warning.assert_not_called()
        mock_response.raise_for_status.assert_not_called()
