"""Unified configuration for FusionTrade AI."""
from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "FusionTrade AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 1999
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:1999",
    ]

    # ── Auth ─────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = f"sqlite:///{ROOT_DIR}/data/fusion_trade.db"

    # ── Redis / Celery ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Email ─────────────────────────────────────────────────────────────
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_ADDRESS: str = ""
    SMTP_USE_SSL: bool = True
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Hugging Face ──────────────────────────────────────────────────────
    HF_TOKEN: str = ""
    HF_LSTM_REPO: str = "rogendo/forex-lstm-models"
    HF_TST_REPO: str = "rogendo/forex-patchtst-models"

    # ── LLM ───────────────────────────────────────────────────────────────
    LLM_PROVIDER: str = "claude"
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # ── Fusion Intelligence ───────────────────────────────────────────────
    FUSION_TIMEFRAMES: List[str] = ["15m", "30m", "1h", "4h"]

    # ── Newsletter ────────────────────────────────────────────────────────
    # Set NEWSLETTER_ENABLED=true in .env to send the daily newsletter automatically.
    # Manual trigger via POST /api/v1/newsletter/trigger always works regardless.
    NEWSLETTER_ENABLED: bool = False

    # ── MT5 (hookable, disabled) ──────────────────────────────────────────
    MT5_ENABLED: bool = False
    MT5_AUTO_EXECUTE: bool = False

    model_config = {"env_file": str(ROOT_DIR / ".env"), "env_file_encoding": "utf-8"}


settings = Settings()
