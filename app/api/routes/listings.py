from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_client, get_current_user

from app.api.schemas.listings import (
    AddOrRemoveWatchlistSchema,
    ListingsResponseSchema,
    ListingResponseSchema,
    CategoriesResponseSchema,
    CreateBidSchema,
    BidsResponseSchema,
    BidResponseSchema,
    AddOrRemoveWatchlistResponseSchema,
)
from app.core.database import get_db
from app.db.managers.base import guestuser_manager
from app.db.managers.listings import (
    listing_manager,
    bid_manager,
    watchlist_manager,
    category_manager,
)
from app.common.exception_handlers import RequestError
from app.db.models.accounts import User
from typing import Optional, Union

from app.db.models.base import GuestUser

router = APIRouter()


@router.get(
    "",
    summary="Retrieve all listings",
    description="This endpoint retrieves all listings",
)
async def retrieve_listings(
    quantity: int = None,
    db: AsyncSession = Depends(get_db),
    client: Optional[Union["User", "GuestUser"]] = Depends(get_client),
) -> ListingsResponseSchema:

    listings = await listing_manager.get_all(db)
    if quantity:
        # Retrieve based on amount
        listings = listings[:quantity]

    data = [
        {
            "watchlist": True
            if await watchlist_manager.get_by_client_id_and_listing_id(
                db, client.id if client else None, listing.id
            )
            else False,
            "time_left_seconds": listing.time_left_seconds,
            **listing.dict(),
        }
        for listing in listings
    ]
    return {"message": "Listings fetched", "data": data}


@router.get(
    "/detail/{slug:str}",
    summary="Retrieve listing's detail",
    description="This endpoint retrieves detail of a listing",
)
async def retrieve_listing_detail(
    slug: str, db: AsyncSession = Depends(get_db)
) -> ListingResponseSchema:
    listing = await listing_manager.get_by_slug(db, slug)
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    related_listings = (
        await listing_manager.get_related_listings(db, listing.category_id, slug)
    )[:3]
    return {
        "message": "Listing details fetched",
        "data": {
            "listing": listing,
            "related_listings": related_listings,
        },
    }


@router.get(
    "/watchlist",
    summary="Retrieve all listings by users watchlist",
    description="This endpoint retrieves all listings",
)
async def retrieve_watchlist(
    db: AsyncSession = Depends(get_db),
    client: Optional[Union["User", "GuestUser"]] = Depends(get_client),
) -> ListingsResponseSchema:
    watchlists = await watchlist_manager.get_by_client_id(
        db, client.id if client else None
    )
    data = [
        {
            "watchlist": True,
            "time_left_seconds": watchlist.listing.time_left_seconds,
            **watchlist.listing.dict(),
        }
        for watchlist in watchlists
    ]
    return {"message": "Watchlist Listings fetched", "data": data}


@router.post(
    "/watchlist",
    summary="Add or Remove listing from a users watchlist",
    description="""
    This endpoint adds or removes a listing from a user's watchlist, authenticated or not.... 
    As a guest, ensure to store guestuser_id in localstorage and keep passing it to header 'guestuserid' in subsequent requests
    """,
    status_code=201,
)
async def add_or_remove_watchlist_listings(
    data: AddOrRemoveWatchlistSchema,
    db: AsyncSession = Depends(get_db),
    client: Optional[Union["User", "GuestUser"]] = Depends(get_client),
) -> AddOrRemoveWatchlistResponseSchema:
    if not client:
        client = await guestuser_manager.create(db, {})

    listing = await listing_manager.get_by_slug(db, data.slug)
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    data_entry = {"session_key": client.id, "listing_id": listing.id}
    if isinstance(client, User):
        # Here we know its a real user and not a session user.
        del data_entry["session_key"]
        data_entry["user_id"] = client.id

    watchlist = await watchlist_manager.get_by_client_id_and_listing_id(
        db, client.id, listing.id
    )
    # If watchlist exists, then its a removal action
    resp_message = "Listing removed from user watchlist"
    status_code = 200
    if not watchlist:
        # If watchlist doesn't exist, then its a addition action
        await watchlist_manager.create(db, data_entry)
        resp_message = "Listing added to user watchlist"
        status_code = 201
    else:
        await watchlist_manager.delete(db, watchlist)

    guestuser_id = client.id if isinstance(client, GuestUser) else None
    return JSONResponse(
        {
            "status": "success",
            "message": resp_message,
            "data": {"guestuser_id": str(guestuser_id) if guestuser_id else None},
        },
        status_code=status_code,
    )


@router.get(
    "/categories",
    summary="Retrieve all categories",
    description="This endpoint retrieves all categories",
)
async def retrieve_categories(
    db: AsyncSession = Depends(get_db),
) -> CategoriesResponseSchema:
    categories = await category_manager.get_all(db)
    return {"message": "Categories fetched", "data": categories}


@router.get(
    "/categories/{slug:str}",
    summary="Retrieve all listings by category",
    description="This endpoint retrieves all listings in a particular category. Use slug 'other' for category other",
)
async def retrieve_category_listings(
    slug: str,
    db: AsyncSession = Depends(get_db),
    client: Optional[Union["User", "GuestUser"]] = Depends(get_client),
) -> ListingsResponseSchema:
    # listings with category 'other' have category column as null
    category = None
    if slug != "other":
        category = await category_manager.get_by_slug(db, slug)
        if not category:
            raise RequestError(err_msg="Invalid category", status_code=404)

    listings = await listing_manager.get_by_category(db, category)
    data = [
        {
            "watchlist": True
            if await watchlist_manager.get_by_client_id_and_listing_id(
                db, client.id if client else None, listing.id
            )
            else False,
            "time_left_seconds": listing.time_left_seconds,
            **listing.dict(),
        }
        for listing in listings
    ]
    return {"message": "Category Listings fetched", "data": data}


@router.get(
    "/detail/{slug:str}/bids",
    summary="Retrieve bids in a listing",
    description="This endpoint retrieves at most 3 bids from a particular listing.",
)
async def retrieve_listing_bids(
    slug: str, db: AsyncSession = Depends(get_db)
) -> BidsResponseSchema:
    listing = await listing_manager.get_by_slug(db, slug)
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    bids = (await bid_manager.get_by_listing_id(db, listing.id))[:3]
    return {
        "message": "Listing Bids fetched",
        "data": {
            "listing": listing.name,
            "bids": bids,
        },
    }


@router.post(
    "/detail/{slug:str}/bids",
    summary="Add a bid to a listing",
    description="This endpoint adds a bid to a particular listing.",
    status_code=201,
)
async def create_bid(
    slug: str,
    data: CreateBidSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BidResponseSchema:
    listing = await listing_manager.get_by_slug(db, slug)
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    amount = data.amount
    bids_count = listing.bids_count
    if user.id == listing.auctioneer_id:
        raise RequestError(err_msg="You cannot bid your own product!", status_code=403)
    elif not listing.active:
        raise RequestError(err_msg="This auction is closed!", status_code=410)
    elif listing.time_left < 1:
        raise RequestError(
            err_msg="This auction is expired and closed!", status_code=410
        )
    elif amount < listing.price:
        raise RequestError(err_msg="Bid amount cannot be less than the bidding price!")
    elif amount <= listing.highest_bid:
        raise RequestError(err_msg="Bid amount must be more than the highest bid!")

    bid = await bid_manager.get_by_user_and_listing_id(db, user.id, listing.id)
    if bid:
        # Update existing bid
        bid = await bid_manager.update(db, bid, {"amount": amount})
    else:
        # Create new bid
        bids_count += 1
        bid = await bid_manager.create(
            db,
            {"user_id": user.id, "listing_id": listing.id, "amount": amount},
        )

    await listing_manager.update(
        db, listing, {"highest_bid": amount, "bids_count": bids_count}
    )
    return {"message": "Bid added to listing", "data": bid}
