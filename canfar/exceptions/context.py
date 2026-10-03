"""Authentication context exceptions."""


class _AuthStateError(Exception):
    """Authentication state failure naming its IDP and the reason."""

    summary = "Auth Context '{idp}' invalid."

    def __init__(self, context: str, reason: str) -> None:
        self.idp = context
        self.message = f"{self.summary.format(idp=context)}\nReason: {reason}"
        super().__init__(self.message)


class AuthContextError(_AuthStateError):
    """Raised when active Authentication state is invalid."""


class AuthRequiredError(AuthContextError):
    """Raised when the active Authentication has no credential to present."""

    summary = "Not authenticated with '{idp}'."


class AuthExpiredError(_AuthStateError):
    """Raised when active Authentication state is expired."""

    summary = "Authentication for '{idp}' expired."
