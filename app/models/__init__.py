# Import all models here so SQLModel.metadata.create_all picks them up
from app.models.user import User
from app.models.journal import PredictionJournal
from app.models.model_registry import ModelRegistry
from app.models.email_verification import EmailVerification
from app.models.password_reset import PasswordReset

__all__ = [
    "User",
    "PredictionJournal",
    "ModelRegistry",
    "EmailVerification",
    "PasswordReset",
]
