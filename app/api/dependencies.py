from fastapi import Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.utils.auth import Authentication
from app.common.exception_handlers import RequestError
from app.core.database import get_db
from app.db.managers.base import guestuser_manager
from app.db.models.accounts import User
from app.db.models.base import GuestUser

jwt_scheme = HTTPBearer()
guest_scheme = APIKeyHeader(
    name="guestuserid",
    description="For guest watchlists. Get ID from '/api/v6/listings/watchlist' POST endpoint",
)


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(jwt_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    print(token)
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
    token: HTTPAuthorizationCredentials = Depends(jwt_scheme),
    guest_id: str = Depends(guest_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[Union[User, GuestUser]]:
    if token:
        user = await get_current_user(token, db)
        return user
    guestuser = await guestuser_manager.get_by_id(db, guest_id)
    return guestuser
