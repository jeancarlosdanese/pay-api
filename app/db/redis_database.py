import logging
import aioredis
from fastapi import FastAPI
from app.core.config import REDIS_HOST, REDIS_DB, REDIS_PORT

logger = logging.getLogger("__name__")


async def connect_to_redis_db(app: FastAPI) -> None:

    try:
        redis = await aioredis.from_url(
            f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
            encoding="utf-8",
            decode_responses=True,
            max_connections=10,
        )
        # await redis.flushdb()  # remove DB
        app.state._redis = redis

    except Exception as e:
        logger.warn("--- REDIS DB CONNECTION ERROR ---")
        logger.warn(e)
        logger.warn("--- REDIS DB CONNECTION ERROR ---")


async def close_redis_db_connection(app: FastAPI) -> None:
    try:
        # await app.state._redis.flushdb()  # remove DB
        await app.state._redis.close()
    except Exception as e:
        logger.warn("--- REDIS DB DISCONNECT ERROR ---")
        logger.warn(e)
        logger.warn("--- REDIS DB DISCONNECT ERROR ---")
