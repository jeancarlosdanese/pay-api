import jwt
from pydantic.error_wrappers import ValidationError
from starlette.status import HTTP_401_UNAUTHORIZED
from app.schemas.token import JWTPayload
from app.core.config import (
    JWT_ALGORITHM,
    JWT_AUDIENCE_FORGOT_PASSWORD,
    SECRET_KEY,
)
from app.db.repositories.tenants import TenantsRepository
from app.schemas.tenant import TenantInDB
from fastapi import HTTPException, Depends, Path, status

from app.schemas.user import UserInDB

from app.db.repositories.users import UsersRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_tenant_by_api_key


async def get_user_by_forgot_password_token_from_path(
    forgot_password_token: str = Path(...),
    secret_key: str = str(SECRET_KEY),
    audience: str = JWT_AUDIENCE_FORGOT_PASSWORD,
    jwt_algorithm: int = JWT_ALGORITHM,
    tenant_host: TenantInDB = Depends(get_tenant_by_api_key),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
) -> UserInDB:
    tenant = await tenants_repo.get_tenant_by_domain(domain=tenant_host.domain)
    if not tenant:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Could not validate host credentials.",
        )

    try:
        decoded_token = jwt.decode(
            forgot_password_token, str(secret_key), audience=audience, algorithms=[jwt_algorithm]
        )
        payload = JWTPayload(**decoded_token)
        user = await users_repo.get_user_by_id(tenant_id=payload.iss, id=payload.sub)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user found with that username.",
            )

        if tenant.id != user.tenant_id:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Could not validate token credentials.",
            )

        return user

    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Could not validate token credentials.",
        )
