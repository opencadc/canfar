"""Static key encryption and decryption using Fernet."""

import base64
import codecs
import hashlib

from cryptography.fernet import Fernet


def derive() -> bytes:
    """Derives a static key for encryption and decryption.

    Returns:
        bytes: The derived key.
    """
    key = hashlib.sha256(b"canfar").digest()
    return base64.urlsafe_b64encode(key)


def encrypt(data: str) -> str:
    """Encrypts the given data using a derived key.

    Args:
        data (str): The data to encrypt.

    Returns:
        str: The encrypted data as a base64-encoded string.
    """
    key = derive()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()


def decrypt(data: str) -> str:
    """Decrypts the given encrypted data using a derived key.

    Args:
        data (str): The encrypted data as a base64-encoded string.

    Returns:
        str: The decrypted data.
    """
    key = derive()
    fernet = Fernet(key)
    decrypted = fernet.decrypt(data.encode())
    return decrypted.decode()


def rot(data: str) -> str:
    """Applies a ROT13 transformation to the given data.

    Args:
        data (str): The data to transform.

    Returns:
        str: The transformed data.
    """
    return codecs.encode(data, "rot_13")


def unrot(data: str) -> str:
    """Reverses a ROT13 transformation on the given data.

    Args:
        data (str): The transformed data.

    Returns:
        str: The original data.
    """
    return codecs.decode(data, "rot_13")
