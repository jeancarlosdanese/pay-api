from fastapi import HTTPException, Depends, Path, status
from pydantic.types import UUID4
from app.schemas.token import Token

from app.db.repositories.contas_bancarias import ContasBancariasRepository
from app.schemas.bancos.conta_bancaria import ContaBancariaInDB
from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_auth_token


async def get_conta_bancaria_by_id_from_path(
    id: UUID4 = Path(..., title="The ID of the conta bancaria to get."),
    user_token: Token = Depends(get_auth_token),
    conta_bancarias_repo: ContasBancariasRepository = Depends(get_repository(ContasBancariasRepository)),
) -> ContaBancariaInDB:
    conta_bancaria = await conta_bancarias_repo.get_conta_bancaria_by_id(tenant_id=user_token.tenant_id, id=id)
    if not conta_bancaria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No conta bancaria found with that id.",
        )

    return conta_bancaria
