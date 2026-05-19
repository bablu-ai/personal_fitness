"""
Auth service — password hashing and JWT operations.

Phase 1 POC: HS256 JWT with a 60-minute expiry and a dev secret.
All Phase 2 hardening TODOs are marked below.
"""
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

# TODO[SECURITY]: move SECRET_KEY to a secrets manager (Doppler / AWS Secrets Manager)
# and rotate on any suspected exposure. Use a 256-bit random value in production.
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# TODO[SECURITY]: add httpOnly refresh token rotation (Phase 2)
# TODO[SECURITY]: add per-IP rate limiting on login/register endpoints (Phase 2)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return bcrypt hash of *password*."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    """Return a signed JWT that expires in ACCESS_TOKEN_EXPIRE_MINUTES minutes."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Decode *token* and return the user_id (sub claim), or None on any error."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        return user_id
    except JWTError:
        return None
