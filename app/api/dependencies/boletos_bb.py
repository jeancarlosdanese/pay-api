from fastapi import HTTPException, Depends, Path, status
from pydantic.types import UUID4
from app.db.repositories.boletos_bb import BoletosBBRepository
from app.schemas.tenant import TenantInDB

from app.schemas.bancos.boleto_bb import BoletoBBInDB
from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_tenant_by_api_key


async def get_boleto_bb_by_id_from_path(
    id: UUID4 = Path(..., title="The ID of the boleto bb to get."),
    tenant_origin: TenantInDB = Depends(get_tenant_by_api_key),
    boletos_bb_repo: BoletosBBRepository = Depends(get_repository(BoletosBBRepository)),
) -> BoletoBBInDB:
    boleto_bb = await boletos_bb_repo.get_boleto_bb_by_id(tenant=tenant_origin, id=id)
    if not boleto_bb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No boleto bb found with that id.",
        )

    return boleto_bb
