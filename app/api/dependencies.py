from typing import Optional, Union
from starlite import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.utils.auth import Authentication
from app.common.exception_handlers import RequestError
from app.db.managers.base import guestuser_manager
from app.db.models.accounts import User
from app.db.models.base import GuestUser


async def get_current_user(request: Request, db: AsyncSession) -> User:
    token = request.headers.get("authorization")
    if not token:
        raise RequestError(
            err_msg="Unauthorized User!",
            status_code=401,
        )
    user = await Authentication.decodeAuthorization(db, token)
    if not user:
        raise RequestError(
            err_msg="Auth Token is Invalid or Expired",
            status_code=401,
        )
    return user


async def get_client(
    request: Request, db: AsyncSession
) -> Optional[Union[User, GuestUser]]:
    token = request.headers.get("authorization")
    if token:
        user = await get_current_user(request, db)
        return user
    guestuser = await guestuser_manager.get_by_id(
        db, request.headers.get("guestuserid")
    )
    return guestuser
