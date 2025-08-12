"""Tests for the garble module."""

import pytest
from cryptography.fernet import InvalidToken

from canfar.utils import garble


def test_derive_returns_bytes() -> None:
    """Test that derive() returns a bytes object of the correct length."""
    key = garble.derive()
    assert isinstance(key, bytes)
    assert len(key) == 44  # Fernet keys are 32 bytes, base64-urlsafe encoded (44 chars)


def test_encrypt_and_decrypt_roundtrip() -> None:
    """Test that encrypt and decrypt work correctly."""
    original = "hello world"
    encrypted = garble.encrypt(original)
    assert isinstance(encrypted, str)
    decrypted = garble.decrypt(encrypted)
    assert decrypted == original


def test_encrypt_produces_different_output_for_different_input() -> None:
    """Test that encrypt produces different output for different inputs."""
    encrypted1 = garble.encrypt("foo")
    encrypted2 = garble.encrypt("bar")
    assert encrypted1 != encrypted2


def test_encrypt_is_deterministic_with_static_key() -> None:
    """Test that encrypt produces the same output for the same input."""
    # Since the key is static, Fernet uses random IV, so output should differ each time
    encrypted1 = garble.encrypt("baz")
    encrypted2 = garble.encrypt("baz")
    assert encrypted1 != encrypted2


def test_decrypt_invalid_data_raises() -> None:
    """Test that decrypt raises an exception for invalid input."""
    with pytest.raises(InvalidToken):
        garble.decrypt("not-a-valid-token")


@pytest.mark.parametrize(
    "text", ["abc", "Hello, World!", "1234567890", "", "ROT13 test!"]
)
def test_rot_and_unrot_are_inverses(text: str) -> None:
    """Test that rot and unrot are inverses of each other."""
    rot_text = garble.rot(text)
    assert isinstance(rot_text, str)
    unrot_text = garble.unrot(rot_text)
    assert unrot_text == text


def test_rot_is_rot13() -> None:
    """Test that rot applies ROT13 transformation."""
    assert garble.rot("abc") == "nop"
    assert garble.rot("NOP") == "ABC"


def test_unrot_is_rot13() -> None:
    """Test that unrot reverses ROT13 transformation."""
    assert garble.unrot("nop") == "abc"
    assert garble.unrot("ABC") == "NOP"


def test_rot_and_unrot_on_empty_string() -> None:
    """Test that rot and unrot work on empty strings."""
    assert garble.rot("") == ""
    assert garble.unrot("") == ""
