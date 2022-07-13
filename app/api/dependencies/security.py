import tldextract
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from app.api.dependencies.database import get_repository
from app.api.dependencies.redis_database import get_redis_repository
from app.core.config import HOST_MAIN, DOMAIN_MAIN
from app.db.repositories.tenant_redis import TenantsRedisRepository
from app.db.repositories.tenants import TenantsRepository
from app.schemas.tenant import TenantInDB, TenantRedis


X_API_KEY = APIKeyHeader(name="X-API-Key", auto_error=True)


async def tenant_authentication_header(
    x_api_key: str = Depends(X_API_KEY),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
    tenants_redis_repo: TenantsRedisRepository = Depends(get_redis_repository(TenantsRedisRepository)),
) -> TenantInDB:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Host not authorized.",
            headers={"WWW-Authenticate": "API-Key"},
        )

    """takes the X-API-Key header and converts it into the matching user object from the database"""
    try:
        tenant = await tenants_redis_repo.get_tenant_by_api_key(api_key=x_api_key)
        if not tenant:
            tenant = await tenants_repo.get_tenant_by_api_key(api_key=x_api_key)
            await tenants_redis_repo.set_tenant_with_with_api_key(tenant=tenant)
            tenant = await tenants_redis_repo.get_tenant_by_api_key(api_key=x_api_key)

        return tenant
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid domain.",
            headers={"WWW-Authenticate": "Domain"},
        )

    # this is where the SQL query for converting the API key into a user_id will go
    tenant = await tenants_repo.get_tenant_by_api_key(api_key=x_api_key)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    return tenant


async def is_domain_main(*, request: Request):
    origin = request.headers.get("origin")

    if not origin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid host of origin",
        )

    tlde = tldextract.extract(origin)
    if f"{tlde.subdomain}.{tlde.domain}.{tlde.suffix}" != f"{HOST_MAIN}.{DOMAIN_MAIN}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid host of origin",
        )

    return origin


async def get_origin(*, request: Request):
    origin = request.headers.get("origin")

    if not origin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid host of origin",
        )

    return origin


async def tenant_by_origin(
    origin: str = Depends(get_origin),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
    tenants_redis_repo: TenantsRedisRepository = Depends(get_redis_repository(TenantsRedisRepository)),
) -> TenantRedis:
    if not origin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Host not authorized.",
            headers={"WWW-Authenticate": "API-Key"},
        )

    tlde = tldextract.extract(origin)
    subdomain = f"{tlde.subdomain}"
    domain = f"{tlde.domain}.{tlde.suffix}"
    if not subdomain or not domain:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid host of origin",
        )

    try:
        tenant = await tenants_redis_repo.get_tenant_by_subdomain_and_domain(subdomain=subdomain, domain=domain)
        if not tenant:
            tenant = await tenants_repo.get_tenant_by_subdomain_and_domain(subdomain=subdomain, domain=domain)
            await tenants_redis_repo.set_tenant_with_subdomain_and_domain(tenant=tenant)
            tenant = await tenants_redis_repo.get_tenant_by_subdomain_and_domain(subdomain=subdomain, domain=domain)

        return tenant
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid domain.",
            headers={"WWW-Authenticate": "Domain"},
        )


async def master_tenant(
    tenant: str = Depends(tenant_by_origin),
) -> TenantRedis:
    if tenant.is_master == "True":
        return tenant

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No valid domain.",
        headers={"WWW-Authenticate": "Domain"},
    )
