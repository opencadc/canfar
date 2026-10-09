"""Session exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from httpx2 import HTTPError


class SessionRequestError(Exception):
    """Raised when one or more session requests fail under errors='raise'.

    Attributes:
        operation: Method name that encountered failures.
        results: Partial or completed results returned under 'ignore'.
        errors: Mapping of session ID or replica number to the original HTTPError.
    """

    def __init__(
        self,
        operation: str,
        results: Any,
        errors: dict[str | int, HTTPError],
    ) -> None:
        """Initialize SessionRequestError.

        Args:
            operation: Name of the session operation.
            results: Results that would have been returned under 'ignore' policy.
            errors: Mapping of session ID or replica index to HTTPError.
        """
        self.operation = operation
        self.results = results
        self.errors = errors
        first_error = next(iter(errors.values())) if errors else None
        if first_error is not None:
            self.__cause__ = first_error
        item_count = len(errors)
        plural = "failure" if item_count == 1 else "failures"
        super().__init__(
            f"{operation} encountered {item_count} {plural}: "
            f"{', '.join(f'{k}: {type(v).__name__}' for k, v in errors.items())}"
        )
