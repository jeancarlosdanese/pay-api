from typing import Optional
from fastapi import Body, Depends, status
from fastapi.routing import APIRouter
from pydantic import UUID4
from app.api.dependencies.contas_bancarias import get_conta_bancaria_by_id_from_path
from app.api.dependencies.database import get_repository
from app.db.repositories.contas_bancarias import ContasBancariasRepository
from app.api.dependencies.auth import has_permission

from app.schemas.bancos.conta_bancaria import (
    ContaBancariaCreate,
    ContaBancariaFull,
    ContaBancariaInDB,
    ContaBancariaUpdate,
)
from app.schemas.filter import FilterModel
from app.schemas.page import PageModel
from app.schemas.token import Token


router = APIRouter()


@router.post(
    "",
    response_model=ContaBancariaFull,
    name="contas-bancarias:register-new-conta-bancaria",
    status_code=status.HTTP_201_CREATED,
)
async def register_new_bank_account(
    user_token: Token = Depends(has_permission(["bank_accounts_manager"])),
    new_bank_account: ContaBancariaCreate = Body(..., embed=False),
    bank_accounts_repo: ContasBancariasRepository = Depends(get_repository(ContasBancariasRepository)),
) -> ContaBancariaFull:
    return await bank_accounts_repo.register_new_back_account(user_token=user_token, new_back_account=new_bank_account)


@router.get(
    "",
    response_model=PageModel,
    name="contas-bancarias:get-all-contas-bancarias",
)
async def get_all_contas_bancarias(
    user_token: Token = Depends(has_permission(["bank_accounts_list"])),
    contas_bancarias_repo: ContasBancariasRepository = Depends(get_repository(ContasBancariasRepository)),
    current_page: int = 1,
    per_page: int = 10,
    nome: Optional[str] = None,
    agencia: Optional[int] = None,
    numero_conta: Optional[int] = None,
    is_active: Optional[bool] = None,
    sorts: Optional[str] = None,
) -> PageModel:
    filters = []
    if nome:
        filters.append(FilterModel(field="nome", operator="ilike", value=f"%{nome}%"))
    if agencia:
        filters.append(FilterModel(field="agencia", operator="eq", value=agencia))
    if numero_conta:
        filters.append(FilterModel(field="numero_conta", operator="eq", value=numero_conta))
    if is_active is not None:
        filters.append(FilterModel(field="is_active", operator="eq", value=is_active))

    return await contas_bancarias_repo.get_all_contas_bancarias(
        tenant_id=user_token.tenant_id, current_page=current_page, per_page=per_page, filters=filters, sorts=sorts
    )


@router.get(
    "/{id}",
    response_model=ContaBancariaFull,
    name="contas-bancarias:get-conta-bancaria-by-id",
)
async def get_conta_bancaria_by_id(
    conta_bancaria: ContaBancariaInDB = Depends(get_conta_bancaria_by_id_from_path),
) -> ContaBancariaFull:
    return conta_bancaria


@router.put(
    "/{id}",
    response_model=ContaBancariaFull,
    name="contas-bancarias:update-conta-bancaria-by-id",
    dependencies=[Depends(has_permission(["bank_accounts_manager"]))],
)
async def uptade_conta_bancaria_by_id(
    conta_bancaria: ContaBancariaInDB = Depends(get_conta_bancaria_by_id_from_path),
    conta_bancaria_update: ContaBancariaUpdate = Body(..., embed=False),
    contas_bancarias_repo: ContasBancariasRepository = Depends(get_repository(ContasBancariasRepository)),
) -> ContaBancariaFull:
    conta_bancaria_updated = await contas_bancarias_repo.update_conta_bancaria_by_id(
        conta_bancaria=conta_bancaria, conta_bancaria_update=conta_bancaria_update
    )

    return conta_bancaria_updated


@router.delete(
    "/{id}",
    response_model=UUID4,
    name="contas-bancarias:delete-conta-bancaria-by-id",
)
async def delete_conta_bancaria_by_id(
    user_token: Token = Depends(has_permission(["bank_accounts_manager"])),
    conta_bancaria: ContaBancariaInDB = Depends(get_conta_bancaria_by_id_from_path),
    contas_bancarias_repo: ContasBancariasRepository = Depends(get_repository(ContasBancariasRepository)),
) -> UUID4:
    return await contas_bancarias_repo.delete_conta_bancaria_by_id(tenant_id=user_token.tenant_id, id=conta_bancaria.id)
