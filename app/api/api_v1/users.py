from app.api.dependencies.redis_database import get_redis_repository
from app.db.repositories.token_redis import TokenRedisRepository
from app.schemas.filter import FilterModel
from typing import Optional, List
from pydantic import UUID4, EmailStr
from fastapi import Path, Depends, APIRouter, Body, HTTPException, status, BackgroundTasks

from app.schemas.page import PageModel
from app.db.repositories.tenants import TenantsRepository
from app.schemas.permission import PermissionsAddToUser, PermissionsDeleteOfUser
from app.schemas.role import RolesAddToUser, RolesDeleteOfUser
from app.api.dependencies.users import get_user_by_id_from_path
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserFull, UserInDB, UserPublic, UserUpdate, UserSummary

from app.db.repositories.users import UsersRepository
from app.api.dependencies.auth import has_permission
from app.api.dependencies.database import get_repository

from app.services.send_email import send_email_in_background_with_template
from app.services import auth_service

router = APIRouter()


@router.post("", response_model=UserFull, name="users:register-new-user", status_code=status.HTTP_201_CREATED)
async def register_new_user(
    background_tasks: BackgroundTasks,
    new_user: UserCreate = Body(..., embed=False),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    tenants_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
    user_token: Token = Depends(has_permission(["users_manager"])),
) -> UserFull:
    if new_user.password != new_user.password_confirmation:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="password and password_confirmation do not match.",
        )

    created_user = await users_repo.register_new_user(tenant_id=user_token.tenant_id, new_user=new_user)
    tenant = await tenants_repo.get_tenant_by_id(id=user_token.tenant_id)

    url_confirm_email = await auth_service.get_url_to_tenant_email_confirm(tenant=tenant, user=created_user)
    send_email_in_background_with_template(
        background_tasks,
        f"Bem vindo à {tenant.name}",
        created_user.email,
        {"name": created_user.full_name.upper(), "url": url_confirm_email},
        "welcome.html",
    )

    return created_user


@router.get(
    "",
    response_model=PageModel,
    name="users:get-all-users",
)
async def get_all_user(
    user_token: Token = Depends(has_permission(["users_list"])),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    current_page: int = 1,
    per_page: int = 10,
    full_name: Optional[str] = None,
    email: Optional[EmailStr] = None,
    username: Optional[str] = None,
    cell_phone: Optional[str] = None,
    sorts: Optional[str] = None,
) -> PageModel:
    filters = []
    if full_name:
        filters.append(FilterModel(field="full_name", operator="ilike", value=f"%{full_name}%"))
    if email:
        filters.append(FilterModel(field="email", operator="eq", value=email))
    if username:
        filters.append(FilterModel(field="username", operator="ilike", value=f"%{username}%"))
    if cell_phone:
        filters.append(FilterModel(field="cell_phone", operator="eq", value=cell_phone))

    return await users_repo.get_all_users(
        tenant_id=user_token.tenant_id, current_page=current_page, per_page=per_page, filters=filters, sorts=sorts
    )


@router.get(
    "/{id}",
    response_model=UserFull,
    name="users:get-user-by-id",
    dependencies=[Depends(has_permission(["users_show"]))],
)
async def get_user_by_id(
    user: UserInDB = Depends(get_user_by_id_from_path),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    return await users_repo.get_full_user_by_user(user=user)


@router.put(
    "/{id}",
    response_model=UserFull,
    name="users:get-user-by-id",
    dependencies=[Depends(has_permission(["users_manager"]))],
)
async def update_user_by_id(
    user: UserInDB = Depends(get_user_by_id_from_path),
    user_update: UserUpdate = Body(..., embed=False),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
) -> UserFull:
    user = await users_repo.update_user(user=user, user_update=user_update)

    # remove all tokens from user
    await token_redis_repo.remove_tokens_by_user_id(user_id=user.id)

    return user


@router.delete(
    "/{id}",
    response_model=UUID4,
    name="users:delete-user-by-id",
    dependencies=[Depends(has_permission(["users_manager"]))],
)
async def delete_user_by_id(
    user: UserInDB = Depends(get_user_by_id_from_path),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
) -> UUID4:
    user_id = await users_repo.delete_user(tenant_id=user.tenant_id, user=user)

    # remove all tokens from user
    await token_redis_repo.remove_tokens_by_user_id(user_id=user_id)

    return user_id


@router.post(
    "/{id}/roles",
    response_model=UserFull,
    name="users:add-roles-to-user-by-id",
    dependencies=[Depends(has_permission(["users_manager"]))],
)
async def add_roles_to_user_by_id(
    user: UserInDB = Depends(get_user_by_id_from_path),
    roles_add_to_user: RolesAddToUser = Body(..., embed=False),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
) -> UserFull:
    await users_repo.register_roles_user(user=user, roles=roles_add_to_user.roles)

    # remove all tokens from user
    await token_redis_repo.remove_tokens_by_user_id(user_id=user.id)

    return await users_repo.get_full_user_by_user(user=user)


@router.delete(
    "/{id}/roles",
    response_model=UserFull,
    name="users:delete-roles-of-user-by-id",
    dependencies=[Depends(has_permission(["users_manager"]))],
)
async def delete_roles_of_user_by_id(
    user: UserInDB = Depends(get_user_by_id_from_path),
    roles_delete_of_user: RolesDeleteOfUser = Body(..., embed=False),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
) -> UserFull:
    await users_repo.delete_roles_user(user=user, roles=roles_delete_of_user.roles)

    # remove all tokens from user
    await token_redis_repo.remove_tokens_by_user_id(user_id=user.id)

    return await users_repo.get_full_user_by_user(user=user)


@router.delete(
    "/{id}/roles/{role_id}",
    response_model=UserFull,
    name="users:delete-role-of-user-by-id_and_role_id",
    dependencies=[Depends(has_permission(["users_manager"]))],
)
async def delete_role_of_user_by_id_and_role_id(
    user: UserInDB = Depends(get_user_by_id_from_path),
    role_id: UUID4 = Path(..., title="The role_id of the roles of user to delete."),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
) -> UserFull:
    await users_repo.delete_roles_user(user=user, roles=[role_id])

    # remove all tokens from user
    await token_redis_repo.remove_tokens_by_user_id(user_id=user.id)

    return await users_repo.get_full_user_by_user(user=user)


@router.post(
    "/{id}/permissions",
    response_model=UserFull,
    name="users:add-permissions-to-user-by-id",
    dependencies=[Depends(has_permission(["users_manager"]))],
)
async def add_permissions_to_user_by_id(
    user: UserInDB = Depends(get_user_by_id_from_path),
    permissions_add_to_user: PermissionsAddToUser = Body(..., embed=False),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
) -> UserFull:
    await users_repo.register_permissions_user(user=user, permissions=permissions_add_to_user.permissions)

    # remove all tokens from user
    await token_redis_repo.remove_tokens_by_user_id(user_id=user.id)

    return await users_repo.get_full_user_by_user(user=user)


@router.delete(
    "/{id}/permissions",
    response_model=UserFull,
    name="users:delete-permissions-of-user-by-id",
    dependencies=[Depends(has_permission(["users_manager"]))],
)
async def delete_permissions_of_user_by_id(
    user: UserInDB = Depends(get_user_by_id_from_path),
    permissions_delete_of_user: PermissionsDeleteOfUser = Body(..., embed=False),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
) -> UserFull:
    await users_repo.delete_permissions_user(user=user, permissions=permissions_delete_of_user.permissions)

    # remove all tokens from user
    await token_redis_repo.remove_tokens_by_user_id(user_id=user.id)

    return await users_repo.get_full_user_by_user(user=user)


@router.delete(
    "/{id}/permissions/{permission_id}",
    response_model=UserFull,
    name="users:delete-permissions-of-user-by-id_and_permission_id",
    dependencies=[Depends(has_permission(["users_manager"]))],
)
async def delete_permissions_of_user_by_id_and_permission_id(
    user: UserInDB = Depends(get_user_by_id_from_path),
    permission_id: UUID4 = Path(..., title="The permission_id of the permissions of user to delete."),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
) -> UserFull:
    await users_repo.delete_permissions_user(user=user, permissions=[permission_id])

    # remove all tokens from user
    await token_redis_repo.remove_tokens_by_user_id(user_id=user.id)

    return await users_repo.get_full_user_by_user(user=user)


@router.get(
    "/get-users-by-role/{slug}",
    response_model=Optional[List[UserSummary]],
    name="users:get-users-by-role",
)
async def get_roles_by_slug(
    slug: str = Path(..., title="The slug role to get users."),
    user_token: Token = Depends(has_permission(["users_manager"])),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> List[UserSummary]:
    return await users_repo.get_users_by_slug_role(tenant_id=user_token.tenant_id, slug=slug)
