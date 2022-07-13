from fastapi import HTTPException, Depends, Path, status
from pydantic.types import UUID4
from app.schemas.token import Token

from app.db.repositories.convenios_bancarios import ConveniosBancariosRepository
from app.schemas.bancos.convenio_bancario import ConvenioBancarioInDB
from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_auth_token


async def get_convenio_bancario_by_id_from_path(
    id: UUID4 = Path(..., title="The ID of the conta bancaria to get."),
    user_token: Token = Depends(get_auth_token),
    convenios_bancarios_repo: ConveniosBancariosRepository = Depends(get_repository(ConveniosBancariosRepository)),
) -> ConvenioBancarioInDB:
    convenio_bancario = await convenios_bancarios_repo.get_convenio_bancario_by_id(
        tenant_id=user_token.tenant_id, id=id
    )
    if not convenio_bancario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No conta bancaria found with that id.",
        )

    return convenio_bancario
