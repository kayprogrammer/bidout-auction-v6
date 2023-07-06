from starlite import Router, Provide
from app.api.routes.general import general_handlers
from app.api.routes.auth import auth_handlers
from app.api.routes.listings import listings_handlers
from app.api.routes.auctioneer import auctioneer_handlers
from app.api.routes.healthcheck import healthcheck
from app.api.dependencies import get_client, get_current_user

general_router = Router(
    path="/api/v6/general",
    route_handlers=general_handlers,
    tags=["General"],
)

auth_router = Router(
    path="/api/v6/auth",
    route_handlers=auth_handlers,
    tags=["Auth"],
    dependencies={
        "user": Provide(get_current_user),
        "client": Provide(get_client),
    },
)

listings_router = Router(
    path="/api/v6/listings",
    route_handlers=listings_handlers,
    tags=["Listings"],
    dependencies={
        "user": Provide(get_current_user),
        "client": Provide(get_client),
    },
)

auctioneer_router = Router(
    path="/api/v6/auctioneer",
    route_handlers=auctioneer_handlers,
    tags=["Auctioneer"],
    dependencies={
        "user": Provide(get_current_user),
    },
)

healthcheck_router = Router(
    path="/api/v6/healthcheck",
    route_handlers=[healthcheck],
    tags=["HealthCheck"],
)

all_routers = [
    general_router,
    auth_router,
    listings_router,
    auctioneer_router,
    healthcheck_router,
]
