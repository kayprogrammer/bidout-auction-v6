from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.general import (
    SubscriberSchema,
    SiteDetailResponseSchema,
    SubscriberResponseSchema,
    ReviewsResponseSchema,
)
from app.core.database import get_db

from app.db.managers.general import (
    sitedetail_manager,
    subscriber_manager,
    review_manager,
)

router = APIRouter()


@router.get(
    "/site-detail",
    summary="Retrieve site details",
    description="This endpoint retrieves few details of the site/application",
)
async def retrieve_site_details(
    db: AsyncSession = Depends(get_db),
) -> SiteDetailResponseSchema:
    sitedetail = await sitedetail_manager.get(db)
    return {"message": "Site Details fetched", "data": sitedetail}


@router.post(
    "/subscribe",
    summary="Add a subscriber",
    description="This endpoint creates a newsletter subscriber in our application",
    status_code=201,
)
async def subscribe(
    data: SubscriberSchema, db: AsyncSession = Depends(get_db)
) -> SubscriberResponseSchema:
    email = data.email
    subscriber = await subscriber_manager.get_by_email(db, email)
    if not subscriber:
        subscriber = await subscriber_manager.create(db, {"email": email})

    return {"message": "Subscription successful", "data": subscriber}


@router.get(
    "/reviews",
    summary="Retrieve site reviews",
    description="This endpoint retrieves a few reviews of the application",
)
async def reviews(db: AsyncSession = Depends(get_db)) -> ReviewsResponseSchema:
    reviews = await review_manager.get_active(db)
    return {"message": "Reviews fetched", "data": reviews}
