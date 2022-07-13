from app.db.repositories.base_redis import BaseRedisRepository
from aioredis import Redis
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES_AUTH, REDIS_PREFIX
from app.schemas.tenant import TenantInDB, TenantRedis


class TenantsRedisRepository(BaseRedisRepository):
    def __init__(self, redis: Redis) -> None:
        super().__init__(redis)

    async def set_tenant_with_subdomain_and_domain(
        self, *, tenant: TenantInDB, expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES_AUTH
    ):
        """
        Set tenant hash fields to multiple values.
        :param tenant:
        """
        tenant_redis = TenantRedis(
            id=str(tenant.id),
            name=tenant.name,
            type=tenant.type.value,
            cpf_cnpj=tenant.cpf_cnpj,
            email=tenant.email,
            subdomain=tenant.subdomain,
            domain=tenant.domain,
            is_master="True" if tenant.is_master else "False",
        )

        key = self.__get_key_by_subdomain_and_domain(subdomain=tenant_redis.subdomain, domain=tenant_redis.domain)
        await self._redis.hmset(key, tenant_redis.dict())
        await self._redis.expire(key, expires_in * 60)  # receive in minutes, need seconds

    async def set_tenant_with_with_api_key(
        self, *, tenant: TenantInDB, expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES_AUTH
    ):
        """
        Set tenant hash fields to multiple values.
        :param tenant:
        """
        tenant_redis = TenantRedis(
            id=str(tenant.id),
            name=tenant.name,
            type=tenant.type.value,
            cpf_cnpj=tenant.cpf_cnpj,
            email=tenant.email,
            subdomain=tenant.subdomain,
            domain=tenant.domain,
            is_master="True" if tenant.is_master else "False",
        )

        key = self.__get_key_by_api_key(api_key=tenant.api_key)
        await self._redis.hmset(key, tenant_redis.dict())
        await self._redis.expire(key, expires_in * 60)  # receive in minutes, need seconds

    async def get_all(self, key: str):
        """
        Get all the fields and values in a hash.
        :param key:
        :return: dict:
        """
        try:
            return await self._redis.hgetall(key)
        except Exception:
            return None

    async def get_tenant_by_subdomain_and_domain(self, subdomain: str, domain: str) -> TenantRedis:
        key = self.__get_key_by_subdomain_and_domain(subdomain=subdomain, domain=domain)
        data = await self.get_all(key)

        if data:
            tenant = TenantRedis(**data)
            return tenant

        return None

    async def get_tenant_by_api_key(self, api_key: str) -> TenantRedis:
        key = self.__get_key_by_api_key(api_key=api_key)
        data = await self.get_all(key)

        if data:
            tenant = TenantRedis(**data)
            return tenant

        return None

    async def remove_tenant_by_subdomain_and_domain(self, subdomain: str, domain: str):
        key = self.__get_key_by_subdomain_and_domain(subdomain, domain)
        tenant = await self.get_tenant_by_subdomain_and_domain(subdomain, domain)

        if tenant:
            await self._redis.delete(f"{REDIS_PREFIX}:{key}")

    async def expire_tenant_by_subdomain_and_domain(self, subdomain: str, domain: str, seconds: int = 60):  # 1min
        key = self.__get_key_by_subdomain_and_domain(subdomain, domain)
        await self._redis.expire(f"{REDIS_PREFIX}:{key}", seconds)

    def __get_key_by_subdomain_and_domain(senf, subdomain: str, domain: str):
        return f"{REDIS_PREFIX}:{subdomain}_{domain.replace('.', '_')}"

    def __get_key_by_api_key(senf, api_key: str):
        return f"{REDIS_PREFIX}:{api_key}"
