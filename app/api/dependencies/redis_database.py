from typing import Callable, Type
from fastapi import Depends
from starlette.requests import Request
from app.db.repositories.base_redis import BaseRedisRepository

from redis.asyncio import Redis


def get_redis_database(request: Request) -> Redis:
    return request.app.state._redis


def get_redis_repository(Repo_type: Type[BaseRedisRepository]) -> Callable:
    def get_repo(redis: Redis = Depends(get_redis_database)) -> Type[BaseRedisRepository]:
        return Repo_type(redis)

    return get_repo
