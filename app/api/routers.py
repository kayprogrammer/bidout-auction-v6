from fastapi import APIRouter
from app.api.routes import general

main_router = APIRouter()
main_router.include_router(general.router, prefix="/general", tags=["General"])
