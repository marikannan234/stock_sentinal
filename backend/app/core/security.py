from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def _pwd_bytes(password: str, max_len: int = 72) -> bytes:
    """Encode password for bcrypt; bcrypt has a 72-byte limit."""
    b = password.encode("utf-8")
    return b[:max_len] if len(b) > max_len else b


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(_pwd_bytes(plain_password), password_hash.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_pwd_bytes(password), bcrypt.gensalt()).decode("utf-8")


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

