from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

# from app.api.routers import api_router
from app.common.exception_handlers import exc_handlers
from app.core.config import settings


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"/openapi.json",
    docs_url="/",
    exception_handlers=exc_handlers,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "x-requested-with",
        "content-type",
        "accept",
        "origin",
        "authorization",
        "guestuserid",
        "accept-encoding",
        "access-control-allow-origin",
        "content-disposition",
    ],
)

# app.include_router(api_router, prefix="/api/v6")


@app.get("/api/v6/healthcheck", name="Healthcheck", tags=["Healthcheck"])
async def healthcheck():
    return {"success": "pong!"}
