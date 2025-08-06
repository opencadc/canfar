"""Tests for the JWT utilities module."""

import base64
import json

import pytest

from skaha.utils.jwt import expiry


def test_expiry_with_valid_jwt() -> None:
    """Test expiry function with a valid JWT token."""
    # Create a mock JWT token with expiry
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"exp": 1234567890, "sub": "user123"}

    # Encode the parts
    header_encoded = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    )
    payload_encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    signature = "fake_signature"

    token = f"{header_encoded}.{payload_encoded}.{signature}"

    result = expiry(token)
    assert result == payload["exp"]


def test_expiry_with_exp_in_header() -> None:
    """Test expiry function when exp is in header (edge case)."""
    # Create a mock JWT token with expiry in header
    header = {"alg": "HS256", "typ": "JWT", "exp": 9876543210}
    payload = {"sub": "user123"}

    # Encode the parts
    header_encoded = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    )
    payload_encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    signature = "fake_signature"

    token = f"{header_encoded}.{payload_encoded}.{signature}"

    result = expiry(token)
    assert result == header["exp"]


def test_expiry_with_no_exp_field() -> None:
    """Test expiry function with JWT token that has no exp field."""
    # Create a mock JWT token without expiry
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": "user123", "iat": 1234567890}

    # Encode the parts
    header_encoded = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    )
    payload_encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    signature = "fake_signature"

    token = f"{header_encoded}.{payload_encoded}.{signature}"

    with pytest.raises(ValueError, match="Failed to decode JWT token"):
        expiry(token)


def test_expiry_with_invalid_json() -> None:
    """Test expiry function with invalid JSON in JWT token."""
    # Create a token with invalid JSON
    header_encoded = base64.urlsafe_b64encode(b"invalid_json").decode().rstrip("=")
    payload_encoded = base64.urlsafe_b64encode(b"also_invalid").decode().rstrip("=")
    signature = "fake_signature"

    token = f"{header_encoded}.{payload_encoded}.{signature}"

    with pytest.raises(ValueError, match="Failed to decode JWT token"):
        expiry(token)
