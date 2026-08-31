import base64
import binascii
import hashlib
import hmac
import os


PBKDF2_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """Hash a password using the application's PBKDF2-SHA256 format."""

    salt = os.urandom(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    return "$".join(
        [
            PBKDF2_ALGORITHM,
            str(PBKDF2_ITERATIONS),
            base64.b64encode(salt).decode("utf-8"),
            base64.b64encode(derived_key).decode("utf-8"),
        ]
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify a password without exposing malformed-hash details."""

    try:
        algorithm, iterations, salt_b64, expected_hash_b64 = (
            encoded_hash.split("$", maxsplit=3)
        )
        if algorithm != PBKDF2_ALGORITHM:
            return False

        salt = base64.b64decode(salt_b64, validate=True)
        expected_hash = base64.b64decode(
            expected_hash_b64,
            validate=True,
        )
        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
    except (binascii.Error, TypeError, ValueError):
        return False

    return hmac.compare_digest(derived_key, expected_hash)
