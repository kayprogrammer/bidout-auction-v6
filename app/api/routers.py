from fastapi import APIRouter
from app.api.routes import general, auth, listings, auctioneer

main_router = APIRouter()
main_router.include_router(general.router, prefix="/general", tags=["General"])
main_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
main_router.include_router(listings.router, prefix="/listings", tags=["Listings"])
main_router.include_router(auctioneer.router, prefix="/auctioneer", tags=["Auctioneer"])
