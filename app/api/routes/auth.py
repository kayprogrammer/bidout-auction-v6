from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_client, get_current_user

from app.api.schemas.auth import (
    RegisterUserSchema,
    VerifyOtpSchema,
    RequestOtpSchema,
    SetNewPasswordSchema,
    LoginUserSchema,
    RefreshTokensSchema,
    RegisterResponseSchema,
    TokensResponseSchema,
)
from app.common.exception_handlers import RequestError
from app.api.schemas.base import ResponseSchema
from app.core.database import get_db
from app.db.managers.base import guestuser_manager

from app.db.models.accounts import User
from app.db.managers.accounts import user_manager, otp_manager, jwt_manager
from app.db.managers.listings import watchlist_manager

from app.api.utils.emails import send_email
from app.core.security import verify_password
from app.api.utils.auth import Authentication
from app.db.models.base import GuestUser

router = APIRouter()


@router.post(
    "/register",
    summary="Register a new user",
    description="This endpoint registers new users into our application",
    status_code=201,
)
async def register(
    background_tasks: BackgroundTasks,
    data: RegisterUserSchema,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponseSchema:
    # Check for existing user
    existing_user = await user_manager.get_by_email(db, data.email)
    if existing_user:
        raise RequestError(
            err_msg="Invalid Entry",
            status_code=422,
            data={"email": "Email already registered!"},
        )

    # Create user
    user = await user_manager.create(db, data.dict())

    # Send verification email
    await send_email(background_tasks, db, user, "activate")

    return {"message": "Registration successful", "data": {"email": user.email}}


@router.post(
    "/verify-email",
    summary="Verify a user's email",
    description="This endpoint verifies a user's email",
    status_code=200,
)
async def verify_email(
    background_tasks: BackgroundTasks,
    data: VerifyOtpSchema,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema:
    user_by_email = await user_manager.get_by_email(db, data.email)

    if not user_by_email:
        raise RequestError(err_msg="Incorrect Email", status_code=404)

    if user_by_email.is_email_verified:
        return ResponseSchema(message="Email already verified")

    otp = await otp_manager.get_by_user_id(db, user_by_email.id)
    if not otp or otp.code != data.otp:
        raise RequestError(err_msg="Incorrect Otp", status_code=404)
    if otp.check_expiration():
        raise RequestError(err_msg="Expired Otp")

    user = await user_manager.update(db, user_by_email, {"is_email_verified": True})
    await otp_manager.delete(db, otp)
    # Send welcome email
    await send_email(background_tasks, db, user, "welcome")
    return {"message": "Account verification successful"}


@router.post(
    "/resend-verification-email",
    summary="Resend Verification Email",
    description="This endpoint resends new otp to the user's email",
)
async def resend_verification_email(
    background_tasks: BackgroundTasks,
    data: RequestOtpSchema,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema:
    user_by_email = await user_manager.get_by_email(db, data.email)
    if not user_by_email:
        raise RequestError(err_msg="Incorrect Email", status_code=404)
    if user_by_email.is_email_verified:
        return {"message": "Email already verified"}

    # Send verification email
    await send_email(background_tasks, db, user_by_email, "activate")

    return {"message": "Verification email sent"}


@router.post(
    "/send-password-reset-otp",
    summary="Send Password Reset Otp",
    description="This endpoint sends new password reset otp to the user's email",
)
async def send_password_reset_otp(
    background_tasks: BackgroundTasks,
    data: RequestOtpSchema,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema:
    user_by_email = await user_manager.get_by_email(db, data.email)
    if not user_by_email:
        raise RequestError(err_msg="Incorrect Email", status_code=404)

    # Send password reset email
    await send_email(background_tasks, db, user_by_email, "reset")
    return {"message": "Password otp sent"}


@router.post(
    "/set-new-password",
    summary="Set New Password",
    description="This endpoint verifies the password reset otp",
)
async def set_new_password(
    background_tasks: BackgroundTasks,
    data: SetNewPasswordSchema,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema:
    email = data.email
    otp_code = data.otp
    password = data.password

    user_by_email = await user_manager.get_by_email(db, email)
    if not user_by_email:
        raise RequestError(err_msg="Incorrect Email", status_code=404)

    otp = await otp_manager.get_by_user_id(db, user_by_email.id)
    if not otp or otp.code != otp_code:
        raise RequestError(err_msg="Incorrect Otp", status_code=404)

    if otp.check_expiration():
        raise RequestError(err_msg="Expired Otp")

    await user_manager.update(db, user_by_email, {"password": password})

    # Send password reset success email
    await send_email(background_tasks, db, user_by_email, "reset-success")

    return {"message": "Password reset successful"}


@router.post(
    "/login",
    summary="Login a user",
    description="This endpoint generates new access and refresh tokens for authentication",
    status_code=201,
)
async def login(
    data: LoginUserSchema,
    client: Optional[Union["User", "GuestUser"]] = Depends(get_client),
    db: AsyncSession = Depends(get_db),
) -> TokensResponseSchema:
    email = data.email
    plain_password = data.password
    user = await user_manager.get_by_email(db, email)
    if not user or verify_password(plain_password, user.password) == False:
        raise RequestError(err_msg="Invalid credentials", status_code=401)

    if not user.is_email_verified:
        raise RequestError(err_msg="Verify your email first", status_code=401)
    await jwt_manager.delete_by_user_id(db, user.id)

    # Create tokens and store in jwt model
    access = await Authentication.create_access_token({"user_id": str(user.id)})
    refresh = await Authentication.create_refresh_token()
    await jwt_manager.create(
        db, {"user_id": user.id, "access": access, "refresh": refresh}
    )

    # Move all guest user watchlists to the authenticated user watchlists
    guest_user_watchlists = await watchlist_manager.get_by_session_key(
        db, client.id if client else None, user.id
    )
    if len(guest_user_watchlists) > 0:
        data_to_create = [
            {"user_id": user.id, "listing_id": listing_id}.copy()
            for listing_id in guest_user_watchlists
        ]
        await watchlist_manager.bulk_create(db, data_to_create)

    if isinstance(client, GuestUser):
        # Delete client (Almost like clearing sessions)
        await guestuser_manager.delete(db, client)

    return {
        "message": "Login successful",
        "data": {"access": access, "refresh": refresh},
    }


@router.post(
    "/refresh",
    summary="Refresh tokens",
    description="This endpoint refresh tokens by generating new access and refresh tokens for a user",
    status_code=201,
)
async def refresh(
    data: RefreshTokensSchema, db: AsyncSession = Depends(get_db)
) -> TokensResponseSchema:
    token = data.refresh
    jwt = await jwt_manager.get_by_refresh(db, token)
    if not jwt:
        raise RequestError(err_msg="Refresh token does not exist", status_code=404)
    if not await Authentication.decode_jwt(token):
        raise RequestError(
            err_msg="Refresh token is invalid or expired", status_code=401
        )

    access = await Authentication.create_access_token({"user_id": str(jwt.user_id)})
    refresh = await Authentication.create_refresh_token()

    await jwt_manager.update(db, jwt, {"access": access, "refresh": refresh})
    return {
        "message": "Tokens refresh successful",
        "data": {"access": access, "refresh": refresh},
    }


@router.get(
    "/logout",
    summary="Logout a user",
    description="This endpoint logs a user out from our application",
)
async def logout(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ResponseSchema:
    await jwt_manager.delete_by_user_id(db, user.id)
    return {"message": "Logout successful"}
