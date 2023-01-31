from typing import List
from app.db.repositories.base_redis import BaseRedisRepository
from redis.asyncio import Redis
from app.schemas.token import Token
from app.core.config import REDIS_PREFIX


class TokenRedisRepository(BaseRedisRepository):
    def __init__(self, redis: Redis) -> None:
        super().__init__(redis)

    async def set_token(self, *, token: Token, expires_in: int):
        """
        Set token hash fields to multiple values.
        :param token:
        """
        await self._redis.hmset(f"{REDIS_PREFIX}:{token.id}", token.dict())
        await self._redis.expire(f"{REDIS_PREFIX}:{token.id}", expires_in * 60)  # receive in minutes, need seconds

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

    async def get_tokens_by_user_id(self, user_id: str) -> List[Token]:
        cursor, keys = await self._redis.scan(match=f"{REDIS_PREFIX}:{user_id}*")
        tokens: List[Token] = []
        for key in keys:
            data = await self._redis.hgetall(key)
            token = Token(**data)
            tokens.append(token)

        return tokens

    async def remove_token_by_key(self, key: str):
        await self._redis.delete(f"{REDIS_PREFIX}:{key}")

    async def expire_token_by_key(self, key: str, seconds: int = 60):  # 1min
        await self._redis.expire(f"{REDIS_PREFIX}:{key}", seconds)

    async def remove_tokens_by_user_id(self, user_id: str):
        tokens: List[Token] = await self.get_tokens_by_user_id(user_id=user_id)
        for token in tokens:
            await self.remove_token_by_key(token.id)

    async def expire_tokens_by_user_id(self, user_id: str):
        tokens: List[Token] = await self.get_tokens_by_user_id(user_id=user_id)
        for token in tokens:
            await self.expire_token_by_key(token.id)
