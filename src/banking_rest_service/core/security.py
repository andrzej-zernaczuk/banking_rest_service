from __future__ import annotations

from passlib.context import CryptContext

# Configure Passlib for bcrypt hashing
# Mark older password hashing schemes as deprecated if a newer, stronger scheme is available in the context.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plain-text password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)
