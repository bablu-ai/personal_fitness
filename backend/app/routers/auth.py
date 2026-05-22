"""
Auth router — register, login, and /me endpoints.

Routes are intentionally thin: they parse requests, delegate to auth_service,
and return responses.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.services import auth_service

router = APIRouter()
_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Dependency: decode Bearer token and return the User row, or raise 401."""
    user_id = auth_service.decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )
    return user


@router.post(
    "/auth/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new user account",
    tags=["auth"],
    responses={409: {"description": "Email already registered"}},
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Create a new user and return an access token."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )
    user = User(
        email=payload.email,
        hashed_password=auth_service.hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = auth_service.create_access_token(user.id)
    return TokenResponse(access_token=token, user_id=user.id)


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Log in with email and password",
    tags=["auth"],
    responses={401: {"description": "Invalid credentials"}},
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Validate credentials and return an access token.

    Returns the same generic 401 for both unknown email and wrong password
    to prevent email enumeration (OWASP A07).
    """
    user = db.query(User).filter(User.email == payload.email).first()
    # Generic error message prevents email enumeration (OWASP A07)
    if not user or not auth_service.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )
    token = auth_service.create_access_token(user.id)
    return TokenResponse(access_token=token, user_id=user.id)


@router.get(
    "/auth/me",
    response_model=UserRead,
    summary="Return the currently authenticated user",
    tags=["auth"],
    responses={401: {"description": "Missing or invalid token"}},
)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the authenticated user's profile."""
    return UserRead.model_validate(current_user)


_get_current_user = get_current_user
