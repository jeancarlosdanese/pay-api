import jwt
from pydantic import ValidationError
from pydantic.types import UUID4
from app.core.config import JWT_ALGORITHM, JWT_AUDIENCE_CONFIRM_EMAIL, SECRET_KEY
from app.schemas.tenant import TenantInDB
from app.api.dependencies.database import get_repository
from app.db.repositories.tenants import TenantsRepository
from fastapi import Depends, Path, HTTPException, status
from app.api.dependencies.auth import has_permission
from app.schemas.token import JWTPayload, Token


async def get_tenant_by_id_from_path(
    id: UUID4 = Path(..., title="The ID of the tenant to get."),
    user_token: Token = Depends(has_permission(["tenants_manager"])),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
) -> TenantInDB:
    tenant_in_db = await tenants_repo.get_tenant_by_id(id=id)
    if not tenant_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tenant found with that id.",
        )
    return tenant_in_db


async def get_tenant_by_email_confirm_token_from_path(
    email_confirm_token: str = Path(...),
    audience: str = JWT_AUDIENCE_CONFIRM_EMAIL,
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
) -> TenantInDB:
    try:
        decoded_token = jwt.decode(email_confirm_token, str(SECRET_KEY), audience=audience, algorithms=[JWT_ALGORITHM])
        payload = JWTPayload(**decoded_token)

        tenant = await tenants_repo.get_tenant_by_id(id=payload.sub)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user found with that tenant.",
            )

        return tenant

    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token credentials.",
        )
