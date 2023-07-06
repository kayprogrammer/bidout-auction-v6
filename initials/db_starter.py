from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.core.database import engine

import logging, asyncio

from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def init() -> None:
    try:
        db = AsyncSessionLocal()
        # Try to create session to check if DB is awake
        await db.execute(text("SELECT 1"))
        await db.close()
    except Exception as e:
        logger.error(e)
        raise e


async def main() -> None:
    logger.info("Initializing service")
    await init()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    asyncio.run(main())
