"""Auth endpoints — register, login, refresh, verify, reset."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import get_current_user, limiter
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth_service import AuthService

router = APIRouter()

REFRESH_COOKIE = "refresh_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=False,   # set True in production behind HTTPS
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: Session = Depends(get_session)):
    svc = AuthService(db)
    try:
        user = svc.register(body.email, body.password, body.full_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, response: Response, db: Session = Depends(get_session)):
    svc = AuthService(db)
    try:
        tokens = svc.login(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    _set_refresh_cookie(response, tokens["refresh_token"])
    return TokenResponse(access_token=tokens["access_token"])


# ── Token refresh ──────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("60/minute")
async def refresh(
    request: Request,
    body: RefreshRequest | None = None,
    response: Response = None,
    db: Session = Depends(get_session),
):
    # Accept token from body OR from httpOnly cookie
    token = None
    if body and body.refresh_token:
        token = body.refresh_token
    else:
        token = request.cookies.get(REFRESH_COOKIE)

    if not token:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    svc = AuthService(db)
    try:
        tokens = svc.refresh(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if response:
        _set_refresh_cookie(response, tokens["refresh_token"])
    return TokenResponse(access_token=tokens["access_token"])


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE)
    return MessageResponse(message="Logged out successfully")


# ── Current user ──────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    svc = AuthService(db)
    try:
        user = svc.update_profile(current_user, full_name=body.full_name, email=str(body.email) if body.email else None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user


# ── Email verification ────────────────────────────────────────────────────────

@router.post("/verify-email", response_model=MessageResponse)
@limiter.limit("10/minute")
async def verify_email(request: Request, body: VerifyEmailRequest, db: Session = Depends(get_session)):
    svc = AuthService(db)
    try:
        svc.verify_email(body.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="Email verified. You can now log in.")


@router.post("/resend-verification", response_model=MessageResponse)
@limiter.limit("2/minute")
async def resend_verification(request: Request, body: ResendVerificationRequest, db: Session = Depends(get_session)):
    svc = AuthService(db)
    svc.resend_verification(str(body.email))
    return MessageResponse(message="If that email is registered and unverified, a new link has been sent.")


# ── Password reset ────────────────────────────────────────────────────────────

@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: Session = Depends(get_session)):
    svc = AuthService(db)
    svc.forgot_password(str(body.email))
    return MessageResponse(message="If that email is registered, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def reset_password(request: Request, body: ResetPasswordRequest, db: Session = Depends(get_session)):
    svc = AuthService(db)
    try:
        svc.reset_password(body.code, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="Password reset successfully. You can now log in.")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    svc = AuthService(db)
    try:
        svc.change_password(current_user, body.current_password, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="Password changed successfully.")
