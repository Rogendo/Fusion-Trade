"""Auth service — registration, login, token refresh, verification, password reset."""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, and_, select

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.email_verification import EmailVerification
from app.models.password_reset import PasswordReset
from app.models.user import User
from app.services.email_service import email_service
from app.config import settings

logger = logging.getLogger(__name__)

VERIFY_CODE_EXPIRY_HOURS = 24
RESET_CODE_EXPIRY_MINUTES = 15


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Register ──────────────────────────────────────────────────────────

    def register(self, email: str, password: str, full_name: str) -> User:
        existing = self._get_user_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        user = User(
            email=email.lower().strip(),
            hashed_password=hash_password(password),
            full_name=full_name.strip(),
            is_verified=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Auto-verify in DEBUG mode when SMTP is not configured
        if settings.DEBUG and not settings.SMTP_USERNAME:
            user.is_verified = True
            self.db.commit()
            self.db.refresh(user)
            logger.info("DEV MODE — auto-verified: %s", user.email)
        else:
            self._send_verification(user)

        logger.info("User registered: %s", user.email)
        return user

    # ── Login ──────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        user = self._get_user_by_email(email.lower().strip())
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is deactivated")
        if not user.is_verified:
            raise ValueError("Please verify your email before logging in")
        logger.info("Login: %s", user.email)
        return self._create_tokens(user)

    # ── Token refresh ──────────────────────────────────────────────────────

    def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise ValueError("Invalid or expired refresh token")
        user_id = payload.get("sub")
        user = self.db.get(User, user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or deactivated")
        return self._create_tokens(user)

    # ── Profile ────────────────────────────────────────────────────────────

    def update_profile(
        self,
        user: User,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> User:
        if email and email.lower().strip() != user.email:
            if self._get_user_by_email(email.lower().strip()):
                raise ValueError("Email already in use")
            user.email = email.lower().strip()
            user.is_verified = False
            if settings.DEBUG and not settings.SMTP_USERNAME:
                user.is_verified = True
            else:
                self._send_verification(user)

        if full_name:
            user.full_name = full_name.strip()

        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return user

    # ── Email verification ─────────────────────────────────────────────────

    def verify_email(self, code: str) -> None:
        now = datetime.now(timezone.utc)
        result = self.db.exec(
            select(EmailVerification).where(
                and_(
                    EmailVerification.code == code,
                    EmailVerification.used == False,  # noqa: E712
                    EmailVerification.expires_at > now,
                )
            )
        ).first()
        if not result:
            raise ValueError("Invalid or expired verification code")

        user = self.db.get(User, result.user_id)
        if not user:
            raise ValueError("User not found")

        user.is_verified = True
        user.updated_at = datetime.now(timezone.utc)
        result.used = True
        self.db.commit()
        logger.info("Email verified: %s", user.email)

    def resend_verification(self, email: str) -> None:
        user = self._get_user_by_email(email.lower().strip())
        if not user or user.is_verified:
            return  # Silently succeed to prevent email enumeration
        if settings.DEBUG and not settings.SMTP_USERNAME:
            user.is_verified = True
            self.db.commit()
        else:
            self._send_verification(user)

    def _send_verification(self, user: User) -> None:
        # Invalidate old unused codes
        old_codes = self.db.exec(
            select(EmailVerification).where(
                and_(
                    EmailVerification.user_id == user.id,
                    EmailVerification.used == False,  # noqa: E712
                )
            )
        ).all()
        for c in old_codes:
            c.used = True

        code = secrets.token_urlsafe(32)
        verification = EmailVerification(
            user_id=user.id,
            code=code,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=VERIFY_CODE_EXPIRY_HOURS),
        )
        self.db.add(verification)
        self.db.commit()
        email_service.send_verification(user.email, code)

    # ── Password reset ─────────────────────────────────────────────────────

    def forgot_password(self, email: str) -> bool:
        user = self._get_user_by_email(email.lower().strip())
        if not user:
            return False  # Silently succeed

        # Invalidate old unused reset codes
        old_resets = self.db.exec(
            select(PasswordReset).where(
                and_(
                    PasswordReset.user_id == user.id,
                    PasswordReset.used == False,  # noqa: E712
                )
            )
        ).all()
        for r in old_resets:
            r.used = True

        code = secrets.token_urlsafe(32)
        reset = PasswordReset(
            user_id=user.id,
            code=code,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=RESET_CODE_EXPIRY_MINUTES),
        )
        self.db.add(reset)
        self.db.commit()

        sent = email_service.send_password_reset(user.email, code)
        logger.info("Password reset for %s — sent: %s", user.email, sent)
        return sent

    def reset_password(self, code: str, new_password: str) -> None:
        now = datetime.now(timezone.utc)
        result = self.db.exec(
            select(PasswordReset).where(
                and_(
                    PasswordReset.code == code,
                    PasswordReset.used == False,  # noqa: E712
                    PasswordReset.expires_at > now,
                )
            )
        ).first()
        if not result:
            raise ValueError("Invalid or expired reset code")

        user = self.db.get(User, result.user_id)
        if not user:
            raise ValueError("User not found")

        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        result.used = True
        self.db.commit()
        logger.info("Password reset: %s", user.email)

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        logger.info("Password changed: %s", user.email)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.exec(select(User).where(User.email == email)).first()

    def _create_tokens(self, user: User) -> dict:
        data = {"sub": user.id, "email": user.email}
        return {
            "access_token": create_access_token(data),
            "refresh_token": create_refresh_token(data),
            "token_type": "bearer",
        }
