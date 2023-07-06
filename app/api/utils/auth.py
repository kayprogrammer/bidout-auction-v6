from sqlalchemy.ext.asyncio import AsyncSession
import random
import string
from datetime import datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.db.managers.accounts import jwt_manager

ALGORITHM = "HS256"


class Authentication:
    # generate random string
    def get_random(length: int):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    # generate access token based and encode user's id
    async def create_access_token(payload: dict):
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode = {"exp": expire, **payload}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    # generate random refresh token
    async def create_refresh_token(
        expire=datetime.utcnow()
        + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    ):
        return jwt.encode(
            {"exp": expire, "data": Authentication.get_random(10)},
            settings.SECRET_KEY,
            algorithm=ALGORITHM,
        )

    # deocde access token from header
    async def decode_jwt(token: str):
        try:
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        except:
            decoded = False
        return decoded

    async def decodeAuthorization(db: AsyncSession, token: str):
        decoded = await Authentication.decode_jwt(token[7:])
        if not decoded:
            return None
        jwt_obj = await jwt_manager.get_by_user_id(db, decoded["user_id"])
        if not jwt_obj:
            return None
        return jwt_obj.user
