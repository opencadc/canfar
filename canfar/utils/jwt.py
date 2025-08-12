"""JWT Related Utilities."""

import base64
import json


def expiry(token: str) -> float:
    """Get the expiry time from a JWT token.

    Args:
        token (str): JWT token.

    Raises:
        ValueError: If token valid or does not contain an expiry time.

    Returns:
        float: Expiry time as Unix timestamp (seconds since epoch).
    """

    def padding(data: str) -> str:
        """Pad the JWT token.

        Args:
            data (str): JWT token.

        Returns:
            str: Padded JWT token.
        """
        return data + "=" * (-len(data) % 4)

    try:
        for part in token.split("."):
            data = base64.urlsafe_b64decode(padding(part)).decode()
            info = json.loads(data)
            if "exp" in info:
                return float(info["exp"])
    except ValueError as err:
        msg = f"Failed to decode JWT token: {err}"
        raise ValueError(msg) from err

    reason = "No expiry time found in JWT token."
    raise ValueError(reason)
