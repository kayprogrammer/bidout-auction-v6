from fastapi import APIRouter
from app.api.routes import general, auth, listings

main_router = APIRouter()
main_router.include_router(general.router, prefix="/general", tags=["General"])
main_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
main_router.include_router(listings.router, prefix="/listings", tags=["Listings"])
