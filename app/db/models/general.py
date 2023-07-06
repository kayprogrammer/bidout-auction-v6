from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import Mapped, relationship

from sqlalchemy.dialects.postgresql import UUID
from uuid import UUID as GUUID  # General UUID
from .base import BaseModel
from .accounts import User


class SiteDetail(BaseModel):
    __tablename__ = "sitedetails"

    name: Mapped[str] = Column(String(300), default="Kay's Auction House")
    email: Mapped[str] = Column(String(300), default="kayprogrammer1@gmail.com")
    phone: Mapped[str] = Column(String(300), default="+2348133831036")
    address: Mapped[str] = Column(String(300), default="234, Lagos, Nigeria")
    fb: Mapped[str] = Column(String(300), default="https://facebook.com")
    tw: Mapped[str] = Column(String(300), default="https://twitter.com")
    wh: Mapped[str] = Column(
        String(300),
        default="https://wa.me/2348133831036",
    )
    ig: Mapped[str] = Column(String(300), default="https://instagram.com")

    def __repr__(self):
        return self.name


class Subscriber(BaseModel):
    __tablename__ = "subscribers"

    email: Mapped[str] = Column(String, unique=True)
    exported: Mapped[bool] = Column(Boolean, default=False)

    def __repr__(self):
        return self.email


class Review(BaseModel):
    __tablename__ = "reviews"

    reviewer_id: Mapped[GUUID] = Column(
        UUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    reviewer: Mapped[User] = relationship("User", lazy="joined")

    show: Mapped[bool] = Column(Boolean, default=False)
    text: Mapped[str] = Column(String(200))

    def __repr__(self):
        return str(self.reviewer_id)
