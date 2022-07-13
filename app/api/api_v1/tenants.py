from typing import Any, List
from pydantic.types import UUID4
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, UploadFile, File, Path, status
from app.api.dependencies.auth import get_tenant_by_token, has_permission

from app.api.dependencies.security import master_tenant
from app.api.dependencies.tenant import get_tenant_by_email_confirm_token_from_path, get_tenant_by_id_from_path
from app.db.repositories.tenant_redis import TenantsRedisRepository

from app.schemas.tenant import TenantCreate, TenantInDB, TenantUpdate, TenantWithUserCreate
from app.db.repositories.tenants import TenantsRepository
from app.db.repositories.users import UsersRepository
from app.db.repositories.roles import RolesRepository
from app.api.dependencies.database import get_repository
from app.schemas.token import Token
from app.schemas.user import UserFullCreate

from app.services import auth_service
from app.services.send_email import send_email_in_background_with_template


router = APIRouter()


@router.get(
    "",
    response_model=List[TenantInDB],
    name="tenants:get-all-tenants",
    dependencies=[
        Depends(master_tenant),
        Depends(has_permission(["tenants_manager"])),
    ],
)
async def get_all_tenants(
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
) -> List[TenantInDB]:
    return await tenants_repo.get_all_tenants()


@router.post(
    "",
    response_model=TenantInDB,
    name="tenants:create-tenant",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(master_tenant)],
)
async def create_new_tenant(
    background_tasks: BackgroundTasks,
    token: Token = Depends(has_permission(["tenants_manager"])),
    new_tenant: TenantWithUserCreate = Body(..., embed=False),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    roles_repo: RolesRepository = Depends(get_repository(RolesRepository)),
) -> TenantInDB:
    if new_tenant.admin_user.password != new_tenant.admin_user.password_confirmation:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="password and password_confirmation do not match.",
        )

    tenant_origin = await tenants_repo.get_tenant_by_id(id=token.tenant_id)
    if not tenant_origin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not authorized for this Tenant.",
        )

    created_tenant = await tenants_repo.create_new_tenant(new_tenant=TenantCreate(**new_tenant.dict()))

    administration = await roles_repo.get_user_by_slug(slug="administration")
    admin_user = await users_repo.register_new_user(
        tenant_id=created_tenant.id,
        new_user=UserFullCreate(
            full_name=new_tenant.admin_user.full_name,
            email=new_tenant.admin_user.email,
            username=new_tenant.admin_user.username,
            password=new_tenant.admin_user.password,
            password_confirmation=new_tenant.admin_user.password_confirmation,
            roles=[str(administration.id)],
        ),
    )
    url_confirm_email = await auth_service.get_url_to_user_email_confirm(
        sub=admin_user.id, tenant_origin=created_tenant
    )
    send_email_in_background_with_template(
        background_tasks,
        f"Bem vindo à {created_tenant.name}",
        admin_user.email,
        {"name": admin_user.full_name.upper(), "url": url_confirm_email},
        "welcome.html",
    )

    url_token = await auth_service.get_url_to_tenant_email_confirm(sub=created_tenant.id, tenant_origin=tenant_origin)

    if url_token:
        send_email_in_background_with_template(
            background_tasks,
            "Forgot password",
            created_tenant.email,
            {"url": url_token, "name": created_tenant.name.upper()},
            "forgot-password.html",
        )

    return created_tenant


@router.post("/confirm-email/{email_confirm_token}", response_model=Any, name="tenants:confirm-email")
async def confirm_email(
    tenant: TenantInDB = Depends(get_tenant_by_email_confirm_token_from_path),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
) -> Any:

    tenant = await tenants_repo.update_email_verified_by_id(id=tenant.id)
    return tenant


@router.get(
    "/{id}",
    response_model=TenantInDB,
    name="tenants:get-tenant-by-id",
    dependencies=[Depends(master_tenant), Depends(has_permission(["tenants_manager"]))],
)
async def get_tenant_by_id(
    id: UUID4 = Path(..., title="The ID of the tenant to get."),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
) -> TenantInDB:
    tenant = await tenants_repo.get_tenant_by_id(id=id)

    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tenant found with that id.")

    return tenant


@router.put(
    "/{id}",
    response_model=TenantInDB,
    name="tenants:update-tenant-by-id",
    dependencies=[Depends(master_tenant), Depends(has_permission(["tenants_manager"]))],
)
async def update_tenant_by_id(
    id: UUID4 = Path(..., title="The ID of the tenant to update."),
    tenant_update: TenantUpdate = Body(..., embed=False),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
    tenants_redis_repo: TenantsRedisRepository = Depends(get_repository(TenantsRedisRepository)),
) -> TenantInDB:
    await tenants_redis_repo.remove_tenant_by_subdomain_and_domain(
        subdomain=tenant_update.subdomain, domain=tenant_update.domain
    )
    updated_tenant = await tenants_repo.update_tenant(id=id, tenant_update=tenant_update)
    if not updated_tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tenant found with that id.")
    return updated_tenant


@router.delete(
    "/{id}",
    response_model=UUID4,
    name="tenants:delete-tenant-by-id",
    dependencies=[Depends(master_tenant), Depends(has_permission(["tenants_manager"]))],
)
async def delete_tenant_by_id(
    id: UUID4 = Path(..., title="The ID of the tenant to delete."),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
    tenants_redis_repo: TenantsRedisRepository = Depends(get_repository(TenantsRedisRepository)),
) -> UUID4:
    tenant = await tenants_repo.get_tenant_by_id(id=id)

    if tenant:
        deleted_id = await tenants_repo.delete_tenant_by_id(id=tenant.id)
        if deleted_id:
            await tenants_redis_repo.remove_tenant_by_subdomain_and_domain(
                subdomain=tenant.subdomain, domain=tenant.domain
            )

        return deleted_id

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tenant found with that id.")


@router.post(
    "/{id}/upload-logo",
    name="tenants:upload-logo",
    dependencies=[Depends(master_tenant), Depends(has_permission(["tenants_manager"]))],
)
async def upload_logo(
    id: UUID4 = Path(..., title="The ID of the tenant to update."),
    file: UploadFile = File(...),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
) -> UUID4:
    tenant = await tenants_repo.get_tenant_by_id(id=id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No tenant found with that id.",
        )

    if not file or file.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="file type must be JPG or PNG type.",
        )

    await tenants_repo.update_logo(tenant_id=id, file=file)

    return id


@router.post(
    "/{id}/send-email-verification",
    name="tenants:send-email-verification",
    dependencies=[Depends(master_tenant), Depends(has_permission(["tenants_manager"]))],
)
async def send_email_verification(
    background_tasks: BackgroundTasks,
    tenant_origin: TenantInDB = Depends(get_tenant_by_token),
    tenant: TenantInDB = Depends(get_tenant_by_id_from_path),
) -> None:
    if not tenant_origin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not authorized for this Tenant.",
        )

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not authorized for this Tenant.",
        )

    url_token = await auth_service.get_url_to_tenant_email_confirm(sub=tenant.id, tenant_origin=tenant_origin)

    if url_token:
        send_email_in_background_with_template(
            background_tasks,
            "Forgot password",
            tenant.email,
            {"url": url_token, "name": tenant.name.upper()},
            "forgot-password.html",
        )
