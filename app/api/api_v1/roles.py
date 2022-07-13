from typing import List
from fastapi import Depends, APIRouter
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Path
from pydantic.types import UUID4
from starlette import status
from app.schemas.role import RoleFull, RoleInDB

from app.db.repositories.roles import RolesRepository
from app.api.dependencies.auth import has_permission
from app.api.dependencies.database import get_repository


router = APIRouter()


@router.get(
    "",
    response_model=List[RoleInDB],
    name="roles:get-all-roles",
    dependencies=[Depends(has_permission(["users_list"]))],
)
async def get_all_role(
    roles_repo: RolesRepository = Depends(get_repository(RolesRepository)),
) -> List[RoleInDB]:
    roles = await roles_repo.get_all_roles()
    return roles


@router.get(
    "/{id}",
    response_model=RoleFull,
    name="roles:get-role-by-id",
    dependencies=[Depends(has_permission(["roles_manager"]))],
)
async def get_role_by_id(
    id: UUID4 = Path(..., title="The ID of the role to get."),
    roles_repo: RolesRepository = Depends(get_repository(RolesRepository)),
) -> RoleFull:
    role = await roles_repo.get_role_by_id(id=id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No role found with that id.",
        )

    return role
