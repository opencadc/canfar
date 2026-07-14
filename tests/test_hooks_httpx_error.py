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

    def test_catch_logs_no_response_body_or_query(self) -> None:
        """HTTP status logs retain safe context without body or query data."""
        query_secret = "query-secret-sentinel"
        body_secret = "body-secret-sentinel"
        request = httpx.Request(
            "GET",
            f"https://url-user:url-pass@example.com/skaha/v1/context?token={query_secret}",
        )
        response = httpx.Response(
            401,
            request=request,
            text=f"provider response {body_secret}",
        )

        with (
            patch("canfar.hooks.httpx.errors.log") as log,
            pytest.raises(httpx.HTTPStatusError),
        ):
            catch(response)

        logged = repr(log.method_calls)
        assert query_secret not in logged
        assert body_secret not in logged
        assert "url-user" not in logged
        assert "url-pass" not in logged
        assert "https://example.com/skaha/v1/context" in logged
        assert "GET" in logged
        assert "401" in logged
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

    def test_catch_read_raises_warning_logged(self) -> None:
        """ReadTimeout from response.read() during body download is warning-logged.

        ``catch`` wraps both ``response.read()`` and ``response.raise_for_status()``
        inside ``_error_handling``, so a body-download ``ReadTimeout`` is caught
        by the shared except ladder and warning-logged before re-raising.
        """
        mock_response = Mock(spec=httpx.Response)
        mock_response.read.side_effect = httpx.ReadTimeout("body download timed out")

        with (
            patch("canfar.hooks.httpx.errors.log") as mock_log,
            pytest.raises(httpx.ReadTimeout),
        ):
            catch(mock_response)

        mock_log.warning.assert_called_once()
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
    async def test_acatch_logs_no_response_body_or_query(self) -> None:
        """Async HTTP status logs retain safe context without body or query data."""
        query_secret = "async-query-secret-sentinel"
        body_secret = "async-body-secret-sentinel"
        request = httpx.Request(
            "POST",
            f"https://url-user:url-pass@example.com/skaha/v1/context?token={query_secret}",
        )
        response = httpx.Response(
            401,
            request=request,
            text=f"provider response {body_secret}",
        )

        with (
            patch("canfar.hooks.httpx.errors.log") as log,
            pytest.raises(httpx.HTTPStatusError),
        ):
            await acatch(response)

        logged = repr(log.method_calls)
        assert query_secret not in logged
        assert body_secret not in logged
        assert "url-user" not in logged
        assert "url-pass" not in logged
        assert "https://example.com/skaha/v1/context" in logged
        assert "POST" in logged
        assert "401" in logged
        assert log.warning.call_args.kwargs["exc_info"] is False

    @pytest.mark.asyncio
    async def test_acatch_aread_raises_warning_logged(self) -> None:
        """ReadTimeout from aread() during body download is warning-logged.

        ``acatch`` wraps both ``await response.aread()`` and
        ``response.raise_for_status()`` inside ``_error_handling``, so a
        body-download ``ReadTimeout`` is caught by the shared except ladder
        and warning-logged before re-raising.
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

        mock_log.warning.assert_called_once()
        mock_response.raise_for_status.assert_not_called()
