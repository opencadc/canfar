from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from canfar.hooks.httpx.errors import acatch, catch

"""Tests for httpx error hooks."""


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
