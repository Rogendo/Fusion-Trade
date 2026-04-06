"""FastAPI dependency injection — current user, rate limiter."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import decode_token
from app.models.user import User

security_scheme = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_session),
) -> User:
    """Decode JWT and return the authenticated user."""
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    return user


def get_current_verified_user(user: User = Depends(get_current_user)) -> User:
    """Like get_current_user but also requires email to be verified."""
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email verification required. Check your inbox.",
        )
    return user
