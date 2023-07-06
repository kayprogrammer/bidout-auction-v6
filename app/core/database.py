from starlite.plugins.sql_alchemy import SQLAlchemyConfig, SQLAlchemyPlugin
from starlite.middleware.session.sqlalchemy_backend import (
    SQLAlchemyBackendConfig,
    create_session_model,
)

from sqlalchemy.ext.declarative import declarative_base
from .config import settings

Base = declarative_base()

sqlalchemy_config = SQLAlchemyConfig(
    connection_string=settings.SQLALCHEMY_DATABASE_URL,
    dependency_key="db",
)

sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

SessionModel = create_session_model(Base)

session_config = SQLAlchemyBackendConfig(
    plugin=sqlalchemy_plugin, model=SessionModel, samesite="none", secure=True
)
