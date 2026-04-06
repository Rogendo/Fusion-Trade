"""SMTP email service — verification, password reset, newsletter."""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def _build_message(self, to: str, subject: str, html: str) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_ADDRESS
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))
        return msg

    def _send(self, to: str, subject: str, html: str) -> bool:
        if not settings.SMTP_USERNAME:
            logger.warning("SMTP not configured — email not sent to %s", to)
            return False
        try:
            msg = self._build_message(to, subject, html)
            if settings.SMTP_USE_SSL:
                ctx = ssl.create_default_context()
                with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, context=ctx) as s:
                    s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    s.sendmail(settings.SMTP_FROM_ADDRESS, to, msg.as_string())
            else:
                with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as s:
                    s.starttls()
                    s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    s.sendmail(settings.SMTP_FROM_ADDRESS, to, msg.as_string())
            logger.info("Email sent to %s: %s", to, subject)
            return True
        except Exception as e:
            logger.error("Failed to send email to %s: %s", to, e)
            return False

    def send_verification(self, to: str, code: str) -> bool:
        verify_url = f"{settings.FRONTEND_URL}/verify-email?code={code}"
        html = f"""
        <h2>Welcome to FusionTrade AI</h2>
        <p>Verify your email to activate your account.</p>
        <p><a href="{verify_url}" style="background:#00ff88;padding:12px 24px;color:#000;text-decoration:none;border-radius:4px;font-weight:bold;">Verify Email</a></p>
        <p>Or paste this code: <code>{code}</code></p>
        <p>This link expires in 24 hours.</p>
        """
        return self._send(to, "Verify your FusionTrade AI account", html)

    def send_password_reset(self, to: str, code: str) -> bool:
        reset_url = f"{settings.FRONTEND_URL}/reset-password?code={code}"
        html = f"""
        <h2>Password Reset — FusionTrade AI</h2>
        <p>You requested a password reset. Click below to set a new password.</p>
        <p><a href="{reset_url}" style="background:#ff4444;padding:12px 24px;color:#fff;text-decoration:none;border-radius:4px;font-weight:bold;">Reset Password</a></p>
        <p>Or paste this code: <code>{code}</code></p>
        <p>This link expires in 15 minutes. If you didn't request this, ignore this email.</p>
        """
        return self._send(to, "Reset your FusionTrade AI password", html)


email_service = EmailService()
