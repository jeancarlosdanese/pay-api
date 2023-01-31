import logging

from redis.asyncio import Redis

logger = logging.getLogger("app")


class BaseRedisRepository:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self.logger = logger
