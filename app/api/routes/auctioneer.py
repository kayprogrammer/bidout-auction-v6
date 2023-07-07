from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user

from app.api.schemas.listings import (
    ListingsResponseSchema,
    BidsResponseSchema,
)

from app.api.schemas.auctioneer import (
    CreateListingSchema,
    UpdateListingSchema,
    CreateListingResponseSchema,
    UpdateProfileSchema,
    UpdateProfileResponseSchema,
    ProfileResponseSchema,
)
from app.common.exception_handlers import RequestError
from app.core.database import get_db
from app.db.managers.listings import (
    category_manager,
    listing_manager,
    bid_manager,
)
from app.db.managers.accounts import user_manager
from app.db.managers.base import file_manager
from app.db.models.accounts import User

router = APIRouter()


@router.get(
    "",
    summary="Get Profile",
    description="This endpoint gets the current user's profile.",
)
async def retrieve_profile(
    user: User = Depends(get_current_user),
) -> ProfileResponseSchema:
    return {"message": "User details fetched!", "data": user}


@router.put(
    "",
    summary="Update Profile",
    description="This endpoint updates an authenticated user's profile. Note: use the returned upload_url to upload avatar to cloudinary",
)
async def update_profile(
    data: UpdateProfileSchema,
    user: "User" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UpdateProfileResponseSchema:
    file_type = data.file_type
    data = data.dict()
    if file_type:
        file = user.avatar
        # Create file object
        if file:
            file = await file_manager.update(
                db, user.avatar, {"resource_type": file_type}
            )
        else:
            file = await file_manager.create(db, {"resource_type": file_type})
        data.update({"avatar_id": file.id})
    data.pop("file_type", None)
    user = await user_manager.update(db, user, data)
    return {"message": "User updated!", "data": user}


@router.get(
    "/listings",
    summary="Retrieve all listings by the current user",
    description="This endpoint retrieves all listings by the current user",
)
async def retrieve_listings(
    user: User = Depends(get_current_user),
    quantity: int = None,
    db: AsyncSession = Depends(get_db),
) -> ListingsResponseSchema:
    listings = await listing_manager.get_by_auctioneer_id(db, user.id)

    if quantity:
        # Retrieve based on amount
        listings = listings[:quantity]
    return {"message": "Auctioneer Listings fetched", "data": listings}


@router.post(
    "/listings",
    summary="Create a listing",
    description="This endpoint creates a new listing. Note: Use the returned upload_url to upload image to cloudinary",
    status_code=201,
)
async def create_listing(
    data: CreateListingSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CreateListingResponseSchema:
    category = data.category

    if not category == "other":
        category = await category_manager.get_by_slug(db, category)
        if not category:
            # Return a data validation error
            raise RequestError(
                err_msg="Invalid entry",
                data={"category": "Invalid category"},
                status_code=422,
            )
    else:
        category = None

    data = data.dict()
    data.update(
        {
            "auctioneer_id": user.id,
            "category_id": category.id if category else None,
        }
    )
    data.pop("category", None)

    # Create file object
    file = await file_manager.create(db, {"resource_type": data["file_type"]})
    data.update({"image_id": file.id})
    data.pop("file_type")

    listing = await listing_manager.create(db, data)
    return {"message": "Listing created successfully", "data": listing}


@router.patch(
    "/listings/{slug:str}",
    summary="Update a listing",
    description="This endpoint update a particular listing.",
)
async def update_listing(
    slug: str,
    data: UpdateListingSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CreateListingResponseSchema:
    category = data.category

    listing = await listing_manager.get_by_slug(db, slug)
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    if user.id != listing.auctioneer_id:
        raise RequestError(err_msg="This listing doesn't belong to you!")

    # Remove keys with values of None
    data = data.dict()
    data = {k: v for k, v in data.items() if v not in (None, "")}

    if category:
        if not category == "other":
            category = await category_manager.get_by_slug(db, category)
            if not category:
                # Return a data validation error
                raise RequestError(
                    err_msg="Invalid entry",
                    data={"category": "Invalid category"},
                    status_code=422,
                )
        else:
            category = None

        data.update({"category_id": category.id if category else None})
        data.pop("category", None)

    file_type = data.get("file_type")
    if file_type:
        file = await file_manager.update(
            db, listing.image, {"resource_type": file_type}
        )
        data.update({"image_id": file.id})
    data.pop("file_type", None)
    listing = await listing_manager.update(db, listing, data)
    return {"message": "Listing updated successfully", "data": listing}


@router.get(
    "/listings/{slug:str}/bids",
    summary="Retrieve all bids in a listing (current user)",
    description="This endpoint retrieves all bids in a particular listing by the current user.",
)
async def retrieve_bids(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BidsResponseSchema:
    # Get listing by slug
    listing = await listing_manager.get_by_slug(db, slug)
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    # Ensure the current user is the listing's owner
    if user.id != listing.auctioneer_id:
        raise RequestError(err_msg="This listing doesn't belong to you!")

    bids = await bid_manager.get_by_listing_id(db, listing.id)
    return {
        "message": "Listing Bids fetched",
        "data": {"listing": listing.name, "bids": bids},
    }
