from typing import Optional, List, Any
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.managers.base import BaseManager
from app.db.models.listings import Category, Listing, WatchList, Bid
from app.api.utils.auth import Authentication

from uuid import UUID
from slugify import slugify


class CategoryManager(BaseManager[Category]):
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Category]:
        category = (
            await db.execute(select(self.model).where(self.model.name == name))
        ).scalar_one_or_none()
        return category

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Category]:
        category = (
            await db.execute(select(self.model).where(self.model.slug == slug))
        ).scalar_one_or_none()
        return category

    async def create(self, db: AsyncSession, obj_in) -> Optional[Category]:
        # Generate unique slug
        created_slug = slugify(obj_in["name"])
        updated_slug = obj_in.get("slug")
        slug = updated_slug if updated_slug else created_slug

        obj_in["slug"] = slug
        slug_exists = await self.get_by_slug(db, slug)
        if slug_exists:
            random_str = Authentication.get_random(4)
            obj_in["slug"] = f"{created_slug}-{random_str}"
            return await self.create(db, obj_in)

        return await super().create(db, obj_in)


class ListingManager(BaseManager[Listing]):
    async def get_all(self, db: AsyncSession) -> Optional[List[Listing]]:
        return (
            (
                await db.execute(
                    select(self.model).order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )

    async def get_by_auctioneer_id(
        self, db: AsyncSession, auctioneer_id: UUID
    ) -> Optional[Listing]:
        return (
            (
                await db.execute(
                    select(self.model)
                    .where(self.model.auctioneer_id == auctioneer_id)
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Listing]:
        listing = (
            await db.execute(select(self.model).where(self.model.slug == slug))
        ).scalar_one_or_none()
        return listing

    async def get_related_listings(
        self, db: AsyncSession, category_id: Any, slug: str
    ) -> Optional[List[Listing]]:
        listings = (
            (
                await db.execute(
                    select(self.model)
                    .where(
                        self.model.category_id == category_id, self.model.slug != slug
                    )
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return listings

    async def get_by_category(
        self, db: AsyncSession, category: Optional[Category]
    ) -> Optional[Listing]:
        if category:
            category = category.id

        listings = (
            (
                await db.execute(
                    select(self.model)
                    .where(self.model.category_id == category)
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return listings

    async def create(self, db: AsyncSession, obj_in) -> Optional[Listing]:
        # Generate unique slug

        created_slug = slugify(obj_in["name"])
        updated_slug = obj_in.get("slug")
        slug = updated_slug if updated_slug else created_slug
        obj_in["slug"] = slug
        slug_exists = await self.get_by_slug(db, slug)
        if slug_exists:
            random_str = Authentication.get_random(4)
            obj_in["slug"] = f"{created_slug}-{random_str}"
            return await self.create(db, obj_in)

        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: Listing, obj_in) -> Listing:
        name = obj_in.get("name")
        if name and name != db_obj.name:
            # Generate unique slug
            created_slug = slugify(name)
            updated_slug = obj_in.get("slug")
            slug = updated_slug if updated_slug else created_slug
            obj_in["slug"] = slug
            slug_exists = await self.get_by_slug(db, slug)
            if slug_exists and not slug == db_obj.slug:
                random_str = Authentication.get_random(4)
                obj_in["slug"] = f"{created_slug}-{random_str}"
                return await self.update(db, db_obj, obj_in)

        return await super().update(db, db_obj, obj_in)


class WatchListManager(BaseManager[WatchList]):
    async def get_by_user_id(
        self, db: AsyncSession, user_id: UUID
    ) -> Optional[List[WatchList]]:
        watchlist = (
            (
                await db.execute(
                    select(self.model)
                    .where(self.model.user_id == user_id)
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return watchlist

    async def get_by_session_key(
        self, db: AsyncSession, session_key: UUID, user_id: UUID
    ) -> Optional[List[WatchList]]:
        subquery = select(self.model.listing_id).where(self.model.user_id == user_id)
        watchlist = (
            (
                await db.execute(
                    select(self.model.listing_id)
                    .where(self.model.session_key == session_key)
                    .where(~self.model.listing_id.in_(subquery))
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return watchlist

    async def get_by_client_id(
        self, db: AsyncSession, client_id: Optional[UUID]
    ) -> Optional[List[WatchList]]:
        if not client_id:
            return []
        watchlist = (
            (
                await db.execute(
                    select(self.model)
                    .where(
                        or_(
                            self.model.user_id == client_id,
                            self.model.session_key == client_id,
                        )
                    )
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return watchlist

    async def get_by_client_id_and_listing_id(
        self, db: AsyncSession, client_id: Optional[UUID], listing_id: UUID
    ) -> Optional[List[WatchList]]:
        if not client_id:
            return None

        watchlist = (
            await db.execute(
                select(self.model)
                .where(
                    or_(
                        self.model.user_id == client_id,
                        self.model.session_key == client_id,
                    )
                )
                .where(self.model.listing_id == listing_id)
            )
        ).scalar_one_or_none()
        return watchlist

    async def create(self, db: AsyncSession, obj_in: dict):
        user_id = obj_in.get("user_id")
        session_key = obj_in.get("session_key")
        listing_id = obj_in["listing_id"]
        key = user_id if user_id else session_key

        # Avoid duplicates
        existing_watchlist = await watchlist_manager.get_by_client_id_and_listing_id(
            db, key, listing_id
        )
        if existing_watchlist:
            return existing_watchlist
        return await super().create(db, obj_in)


class BidManager(BaseManager[Bid]):
    async def get_by_user_id(
        self, db: AsyncSession, user_id: UUID
    ) -> Optional[List[Bid]]:
        bids = (
            (
                await db.execute(
                    select(self.model)
                    .where(self.model.user_id == user_id)
                    .order_by(self.model.updated_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return bids

    async def get_by_listing_id(
        self, db: AsyncSession, listing_id: UUID
    ) -> Optional[List[Bid]]:
        bids = (
            (
                await db.execute(
                    select(self.model)
                    .where(self.model.listing_id == listing_id)
                    .order_by(self.model.updated_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return bids

    async def get_by_user_and_listing_id(
        self, db: AsyncSession, user_id: UUID, listing_id: UUID
    ) -> Optional[Bid]:
        bid = (
            await db.execute(
                select(self.model).where(
                    self.model.user_id == user_id, self.model.listing_id == listing_id
                )
            )
        ).scalar_one_or_none()
        return bid

    async def create(self, db: AsyncSession, obj_in: dict):
        user_id = obj_in["user_id"]
        listing_id = obj_in["listing_id"]

        existing_bid = await bid_manager.get_by_user_and_listing_id(
            db, user_id, listing_id
        )
        if existing_bid:
            obj_in.pop("user_id", None)
            obj_in.pop("listing_id", None)
            return await self.update(db, existing_bid, obj_in)

        new_bid = await super().create(db, obj_in)
        return new_bid


# How to use
category_manager = CategoryManager(Category)
listing_manager = ListingManager(Listing)
watchlist_manager = WatchListManager(WatchList)
bid_manager = BidManager(Bid)


# this can now be used to perform any available crud actions e.g category_manager.get_by_id(db=db, id=id)
