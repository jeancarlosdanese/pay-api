from typing import Optional
from fastapi import Body, Depends, status
from fastapi.routing import APIRouter
from pydantic import UUID4
from app.api.dependencies.convenios_bancarios import get_convenio_bancario_by_id_from_path
from app.api.dependencies.database import get_repository
from app.db.repositories.convenios_bancarios import ConveniosBancariosRepository
from app.api.dependencies.auth import has_permission

from app.schemas.bancos.convenio_bancario import (
    ConvenioBancarioCreate,
    ConvenioBancarioFull,
    ConvenioBancarioInDB,
    ConvenioBancarioUpdate,
)
from app.schemas.filter import FilterModel
from app.schemas.page import PageModel
from app.schemas.token import Token


router = APIRouter()


@router.post(
    "",
    response_model=ConvenioBancarioFull,
    name="convenios-bancarios:register-new-convenio-bancario",
    status_code=status.HTTP_201_CREATED,
)
async def register_new_bank_account(
    user_token: Token = Depends(has_permission(["bank_accounts_manager"])),
    new_bank_account: ConvenioBancarioCreate = Body(..., embed=False),
    bank_accounts_repo: ConveniosBancariosRepository = Depends(get_repository(ConveniosBancariosRepository)),
) -> ConvenioBancarioFull:
    return await bank_accounts_repo.register_new_back_account(user_token=user_token, new_back_account=new_bank_account)


@router.get(
    "",
    response_model=PageModel,
    name="convenios-bancarios:get-all-convenios-bancarios",
)
async def get_all_convenios_bancarios(
    user_token: Token = Depends(has_permission(["bank_accounts_list"])),
    convenios_bancarios_repo: ConveniosBancariosRepository = Depends(get_repository(ConveniosBancariosRepository)),
    current_page: int = 1,
    per_page: int = 10,
    numero_convenio: Optional[int] = None,
    numero_carteira: Optional[int] = None,
    numero_variacao_carteira: Optional[int] = None,
    nome_conta: Optional[str] = None,
    numero_conta: Optional[int] = None,
    is_active: Optional[bool] = None,
    sorts: Optional[str] = None,
) -> PageModel:
    filters = []
    if numero_convenio:
        filters.append(
            FilterModel(table="convenios_bancarios", field="numero_convenio", operator="eq", value=numero_convenio)
        )
    if numero_carteira:
        filters.append(
            FilterModel(table="convenios_bancarios", field="numero_carteira", operator="eq", value=numero_carteira)
        )
    if numero_variacao_carteira:
        filters.append(
            FilterModel(
                table="convenios_bancarios",
                field="numero_variacao_carteira",
                operator="eq",
                value=numero_variacao_carteira,
            )
        )
    if nome_conta:
        filters.append(
            FilterModel(
                table="contas_bancarias",
                field="nome",
                alias_field="nome_conta",
                operator="ilike",
                value=f"%{nome_conta}%",
            )
        )
    if numero_conta:
        filters.append(FilterModel(table="contas_bancarias", field="numero_conta", operator="eq", value=numero_conta))
    if is_active is not None:
        filters.append(FilterModel(table="convenios_bancarios", field="is_active", operator="eq", value=is_active))

    return await convenios_bancarios_repo.get_all_convenios_bancarios(
        tenant_id=user_token.tenant_id, current_page=current_page, per_page=per_page, filters=filters, sorts=sorts
    )


@router.get(
    "/{id}",
    response_model=ConvenioBancarioFull,
    name="contas-bancaris:get-convenio-bancario-by-id",
)
async def get_convenio_bancario_by_id(
    convenio_bancario: ConvenioBancarioInDB = Depends(get_convenio_bancario_by_id_from_path),
) -> ConvenioBancarioFull:
    return convenio_bancario


@router.put(
    "/{id}",
    response_model=ConvenioBancarioFull,
    name="contas-bancaris:update-convenio-bancario-by-id",
    dependencies=[Depends(has_permission(["bank_accounts_manager"]))],
)
async def uptade_convenio_bancario_by_id(
    convenio_bancario: ConvenioBancarioInDB = Depends(get_convenio_bancario_by_id_from_path),
    convenio_bancario_update: ConvenioBancarioUpdate = Body(..., embed=False),
    convenios_bancarios_repo: ConveniosBancariosRepository = Depends(get_repository(ConveniosBancariosRepository)),
) -> ConvenioBancarioFull:
    convenio_bancario_updated = await convenios_bancarios_repo.update_convenio_bancario_by_id(
        convenio_bancario=convenio_bancario, convenio_bancario_update=convenio_bancario_update
    )

    return convenio_bancario_updated


@router.delete(
    "/{id}",
    response_model=UUID4,
    name="contas-bancaris:delete-convenio-bancario-by-id",
)
async def delete_convenio_bancario_by_id(
    user_token: Token = Depends(has_permission(["bank_accounts_manager"])),
    convenio_bancario: ConvenioBancarioInDB = Depends(get_convenio_bancario_by_id_from_path),
    convenios_bancarios_repo: ConveniosBancariosRepository = Depends(get_repository(ConveniosBancariosRepository)),
) -> UUID4:
    return await convenios_bancarios_repo.delete_convenio_bancario_by_id(
        tenant_id=user_token.tenant_id, id=convenio_bancario.id
    )
