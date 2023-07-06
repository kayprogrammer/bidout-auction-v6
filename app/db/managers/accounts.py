from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.managers.base import BaseManager
from app.db.models.accounts import Jwt, Otp, User
from uuid import UUID
import random


class UserManager(BaseManager[User]):
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        user = (
            await db.execute(select(self.model).where(self.model.email == email))
        ).scalar_one_or_none()
        return user

    async def create(self, db: AsyncSession, obj_in) -> User:
        # hash the password
        obj_in.update({"password": get_password_hash(obj_in["password"])})
        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: User, obj_in) -> Optional[User]:
        # hash the password
        password = obj_in.get("password")
        if password:
            obj_in["password"] = get_password_hash(password)
        user = await super().update(db, db_obj, obj_in)
        return user


class OtpManager(BaseManager[Otp]):
    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Optional[Otp]:
        otp = (
            await db.execute(select(self.model).where(self.model.user_id == user_id))
        ).scalar_one_or_none()
        return otp

    async def create(self, db: AsyncSession, obj_in) -> Optional[Otp]:
        code = random.randint(100000, 999999)
        obj_in.update({"code": code})
        existing_otp = await self.get_by_user_id(db, obj_in["user_id"])
        if existing_otp:
            return await self.update(db, existing_otp, {"code": code})
        return await super().create(db, obj_in)


class JwtManager(BaseManager[Jwt]):
    async def get_by_user_id(self, db: AsyncSession, user_id: str) -> Optional[Jwt]:
        jwt = (
            await db.execute(select(self.model).where(self.model.user_id == user_id))
        ).scalar_one_or_none()
        return jwt

    async def get_by_refresh(self, db: AsyncSession, refresh: str) -> Optional[Jwt]:
        jwt = (
            await db.execute(select(self.model).where(self.model.refresh == refresh))
        ).scalar_one_or_none()
        return jwt

    async def delete_by_user_id(self, db: AsyncSession, user_id: UUID):
        jwt = (
            await db.execute(select(self.model).where(self.model.user_id == user_id))
        ).scalar_one_or_none()
        await self.delete(db, jwt)


# How to use
user_manager = UserManager(User)
otp_manager = OtpManager(Otp)
jwt_manager = JwtManager(Jwt)


# this can now be used to perform any available crud actions e.g user_manager.get_by_id(db=db, id=id)
