import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped

from app.core.database import Base


class BaseModel(Base):
    __abstract__ = True
    pkid: Mapped[int] = Column(Integer, primary_key=True)
    id: Mapped[uuid.UUID] = Column(UUID(), default=uuid.uuid4, unique=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = Column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    def dict(self):
        return self.__dict__


class File(BaseModel):
    __tablename__ = "files"

    resource_type: Mapped[str] = Column(String)


class GuestUser(BaseModel):
    __tablename__ = "guestusers"
