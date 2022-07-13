from typing import List
from app.db.repositories.base_redis import BaseRedisRepository
from aioredis import Redis
from app.schemas.token_bb import TokenBB
from app.core.config import REDIS_PREFIX


class TokenBBRedisRepository(BaseRedisRepository):
    def __init__(self, redis: Redis) -> None:
        super().__init__(redis)

    async def set_token(self, *, token: TokenBB, expires_in: int):
        """
        Set token hash fields to multiple values.
        :param token:
        """
        await self._redis.hmset(f"{REDIS_PREFIX}:{token.id}", token.dict())
        await self._redis.expire(f"{REDIS_PREFIX}:{token.id}", expires_in)  # need seconds

    async def len(self, key: str):
        """
        Get the number of fields in a given hash.
        :param key:
        :return: int:
        """
        return await self._redis.hlen(f"{REDIS_PREFIX}:{key}")

    async def get_all(self, key: str):
        """
        Get all the fields and values in a hash.
        :param key:
        :return: dict:
        """
        return await self._redis.hgetall(f"{REDIS_PREFIX}:{key}")

    async def get_token_by_id(self, id: str) -> List[TokenBB]:
        data = await self._redis.hgetall(f"{REDIS_PREFIX}:{id}")

        if not data:
            return None

        token = TokenBB(**data)

        return token

    async def remove_token_by_key(self, key: str):
        await self._redis.delete(f"{REDIS_PREFIX}:{key}")

    async def expire_token_by_key(self, key: str, seconds: int = 60):  # 1min
        await self._redis.expire(f"{REDIS_PREFIX}:{key}", seconds)

    async def remove_tokens_by_id(self, id: str):
        tokens: List[TokenBB] = await self.get_tokens_by_id(id=id)
        for token in tokens:
            await self.remove_token_by_key(token.id)

    async def expire_tokens_by_id(self, id: str):
        tokens: List[TokenBB] = await self.get_tokens_by_id(id=id)
        for token in tokens:
            await self.expire_token_by_key(token.id)
