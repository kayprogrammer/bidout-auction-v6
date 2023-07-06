import asyncio, os, sys

sys.path.append(os.path.abspath("./"))  # To single-handedly execute this script

import logging

from initials.data_script import CreateData
from app.core.database import engine
from sqlalchemy.ext.asyncio import async_sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init() -> None:
    db = SessionLocal()
    create_data = CreateData(db)
    await create_data.initialize()
    await db.close()


async def main() -> None:
    logger.info("Creating initial data")
    await init()
    logger.info("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
