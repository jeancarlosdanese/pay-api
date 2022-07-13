from typing import List
from fastapi import Depends, APIRouter
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Path
from pydantic.types import UUID4
from starlette import status
from app.schemas.permission import PermissionInDB

from app.db.repositories.permissions import PermissionsRepository
from app.api.dependencies.auth import has_permission
from app.api.dependencies.database import get_repository


router = APIRouter()


@router.get(
    "",
    response_model=List[PermissionInDB],
    name="permissions:get-all-permissions",
    dependencies=[Depends(has_permission(["users_list"]))],
)
async def get_all_permission(
    permissions_repo: PermissionsRepository = Depends(get_repository(PermissionsRepository)),
) -> List[PermissionInDB]:
    permissions = await permissions_repo.get_all_permissions()
    return permissions


@router.get(
    "/{id}",
    response_model=PermissionInDB,
    name="permissions:get-permission-by-id",
    dependencies=[Depends(has_permission(["permissions_manager"]))],
)
async def get_permission_by_id(
    id: UUID4 = Path(..., title="The ID of the permission to get."),
    permissions_repo: PermissionsRepository = Depends(get_repository(PermissionsRepository)),
) -> PermissionInDB:
    permission = await permissions_repo.get_permission_by_id(id=id)

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No permission found with that id.",
        )

    return permission
