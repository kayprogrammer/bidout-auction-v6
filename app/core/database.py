from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .config import settings

Base = declarative_base()

engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
