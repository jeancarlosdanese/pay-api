import logging
from user_agents import parse

from starlette.requests import Request

from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.api.dependencies.redis_database import get_redis_repository
from app.core.config import JWT_AUDIENCE_AUTH, JWT_AUDIENCE_CONFIRM_EMAIL, SECRET_KEY, API_PREFIX_V1
from app.db.repositories.token_redis import TokenRedisRepository
from app.schemas.tenant import TenantInDB
from app.schemas.token import JWTPayloadAuth, Token
from app.schemas.user import UserInDB
from app.api.dependencies.database import get_repository
from app.db.repositories.users import UsersRepository
from app.db.repositories.tenants import TenantsRepository
from app.services import auth_service

logger = logging.getLogger("app")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX_V1}/auth/login/token/")


async def get_user_agent(
    *,
    request: Request,
) -> str:
    user_agent = parse((request.headers["user-agent"]))
    if user_agent.is_bot:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication was unsuccessful.",
        )

    user_agent_str = f"{user_agent.device.family}-{user_agent.os.family}-{user_agent.browser.family}".replace(" ", "_")

    return user_agent_str


async def get_tenant_by_api_key(
    *,
    request: Request,
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
) -> Optional[TenantInDB]:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        tenant = await tenants_repo.get_tenant_by_api_key(api_key=api_key)
        if tenant and tenant.is_active:
            return tenant

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Host not authorized.",
        headers={"WWW-Authenticate": "API-Key"},
    )


async def get_auth_token(
    token: str = Depends(oauth2_scheme),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
) -> Optional[Token]:
    token_data = auth_service.get_token_data_from_token(
        token=token, secret_key=str(SECRET_KEY), audience=str(JWT_AUDIENCE_AUTH)
    )
    try:
        redis_token = await token_redis_repo.get_all(token_data.sub)
        user_token = Token(**redis_token)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authenticated user.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_token


async def get_tenant_by_token(
    token: Token = Depends(get_auth_token),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
) -> Optional[TenantInDB]:
    tenant = await tenants_repo.get_tenant_by_id(id=token.tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authenticated user.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return tenant


def has_roles(slugs: List[str]) -> Optional[Token]:
    async def can_roles(
        token: Token = Depends(get_auth_token),
    ) -> Optional[UserInDB]:
        roles = token.roles.split(",")
        has_roles = [s for s in slugs if s in roles]

        if not has_roles:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized user.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token

    return can_roles


def has_permission(slugs: List[str]) -> Optional[Token]:
    async def can_permission(token: Token = Depends(get_auth_token)) -> Optional[Token]:
        permissions = token.permissions.split(",")
        has_permissions = [s for s in slugs if s in permissions]

        if not has_permissions:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized user.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return token

    return can_permission


def get_user_from_forgot_password_token(forgot_password_token: str) -> Optional[UserInDB]:
    async def get_user(
        users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
        tenants_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    ) -> Optional[UserInDB]:
        user_data = auth_service.get_user_data_from_forgot_password_token(
            forget_password_token=forgot_password_token, secret_key=str(SECRET_KEY)
        )
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized user.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_data

    return get_user()


def get_user_from_confirm_email_token(confirm_email_token: str) -> Optional[JWTPayloadAuth]:
    payload: JWTPayloadAuth = auth_service.get_token_data_from_token(
        token=confirm_email_token, secret_key=str(SECRET_KEY), audience=str(JWT_AUDIENCE_CONFIRM_EMAIL)
    )
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authenticated user.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
