"""Authentication context exceptions."""


class AuthContextError(Exception):
    """Raised when active Authentication state is invalid."""

    def __init__(self, context: str, reason: str) -> None:
        self.message = f"Auth Context '{context}' invalid."
        self.message += f"\nReason: {reason}"
        super().__init__(self.message)


class AuthExpiredError(Exception):
    """Raised when active Authentication state is expired."""

    def __init__(self, context: str, reason: str) -> None:
        self.message = f"Auth Context '{context}' expired."
        self.message += f"\nReason: {reason}"
        super().__init__(self.message)
