from pydantic.types import UUID4
from app.api.dependencies.security import tenant_by_origin
from app.schemas.area import AreaInDB
from app.api.dependencies.database import get_repository
from app.db.repositories.areas import AreasRepository
from app.schemas.tenant import TenantRedis
from fastapi import Depends, Path, HTTPException, status


async def get_area_by_id_from_path(
    id: UUID4 = Path(..., title="The ID of the area to get."),
    tenant: TenantRedis = Depends(tenant_by_origin),
    areas_repo: AreasRepository = Depends(get_repository(AreasRepository)),
) -> AreaInDB:
    area_in_db = await areas_repo.get_area_by_id(tenant_id=tenant.id, id=id)
    if not area_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No area found with that id.",
        )

    return area_in_db
