from app.db.redis_database import close_redis_db_connection, connect_to_redis_db
from typing import Callable
from fastapi import FastAPI
from app.db.database import connect_to_db, close_db_connection


def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        await connect_to_db(app)
        await connect_to_redis_db(app)

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        await close_db_connection(app)
        await close_redis_db_connection(app)

    return stop_app
