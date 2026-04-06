"""Email verification token — single-use, 24h expiry."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class EmailVerification(SQLModel, table=True):
    __tablename__ = "email_verifications"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
    )
    user_id: str = Field(foreign_key="users.id", index=True)
    code: str = Field(unique=True, index=True, max_length=64)
    used: bool = Field(default=False)
    expires_at: datetime
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
