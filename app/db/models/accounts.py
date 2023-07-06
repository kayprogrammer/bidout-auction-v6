from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped

from .base import BaseModel, File
from datetime import datetime
from app.core.config import settings

from uuid import UUID as GUUID  # General UUID


class User(BaseModel):
    __tablename__ = "users"
    first_name: Mapped[str] = Column(String(50))
    last_name: Mapped[str] = Column(String(50))

    email: Mapped[str] = Column(String(), unique=True)

    password: Mapped[str] = Column(String())
    is_email_verified: Mapped[bool] = Column(Boolean(), default=False)
    is_superuser: Mapped[bool] = Column(Boolean(), default=False)
    is_staff: Mapped[bool] = Column(Boolean(), default=False)
    terms_agreement: Mapped[bool] = Column(Boolean(), default=False)

    avatar_id: Mapped[GUUID] = Column(
        UUID(),
        ForeignKey("files.id", ondelete="CASCADE"),
        unique=True,
    )
    avatar: Mapped[File] = relationship("File", lazy="joined")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return self.full_name


class Jwt(BaseModel):
    __tablename__ = "jwts"
    user_id: Mapped[GUUID] = Column(
        UUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    user: Mapped[User] = relationship("User", lazy="joined")
    access: Mapped[str] = Column(String())
    refresh: Mapped[str] = Column(String())

    def __repr__(self):
        return f"Access - {self.access} | Refresh - {self.refresh}"


class Otp(BaseModel):
    __tablename__ = "otps"
    user_id: Mapped[GUUID] = Column(
        UUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    user: Mapped[User] = relationship("User", lazy="joined")
    code: Mapped[int] = Column(Integer())

    def __repr__(self):
        return f"User - {self.user.full_name} | Code - {self.code}"

    def check_expiration(self):
        now = datetime.utcnow()
        diff = now - self.updated_at
        if diff.total_seconds() > settings.EMAIL_OTP_EXPIRE_SECONDS:
            return True
        return False
