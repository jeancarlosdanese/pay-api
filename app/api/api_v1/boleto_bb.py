import httpx
from datetime import date
from typing import Any, Optional
from pydantic import condecimal, conint, constr
from app.api.dependencies.database import get_repository
from fastapi import Body, Depends, HTTPException, status
from app.api.dependencies.redis_database import get_redis_repository
from app.db.repositories.boletos_bb import BoletosBBRepository
from app.db.repositories.convenios_bancarios import ConveniosBancariosRepository
from app.db.repositories.contas_bancarias import ContasBancariasRepository
from app.db.repositories.token_bb_redis import TokenBBRedisRepository
from app.schemas.bancos.boleto import BoletoCreate
from app.schemas.enums import PersonType
from app.schemas.filter import FilterModel
from app.schemas.page import PageModel

from app.schemas.tenant import TenantInDB
from fastapi.routing import APIRouter
from app.api.dependencies.auth import get_tenant_by_api_key
from app.util.validators import validate_cpf_cnpj


router = APIRouter()
client = httpx.AsyncClient()


@router.post("", response_model=Any, name="boletos-bb:register-new-boleto-bb", status_code=status.HTTP_201_CREATED)
async def register_new_boleto_bb(
    new_boleto: BoletoCreate = Body(..., embed=False),
    convenios_bancarios_repo: ConveniosBancariosRepository = Depends(get_repository(ConveniosBancariosRepository)),
    contas_bancarias_repo: ContasBancariasRepository = Depends(get_repository(ContasBancariasRepository)),
    token_bb_redis_repo: TokenBBRedisRepository = Depends(get_redis_repository(TokenBBRedisRepository)),
    boletos_bb_repo: BoletosBBRepository = Depends(get_repository(BoletosBBRepository)),
    tenant_origin: TenantInDB = Depends(get_tenant_by_api_key),
) -> Any:
    convenio_bancario = await convenios_bancarios_repo.get_convenio_bancario_by_id(
        tenant_id=tenant_origin.id, id=new_boleto.convenio_bancario_id
    )
    if not convenio_bancario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That convenio_bancario_id is not found. Please try another one.",
        )

    conta_bancaria = await contas_bancarias_repo.get_conta_bancaria_by_id(
        tenant_id=tenant_origin.id,
        id=convenio_bancario.conta_bancaria_id,
    )

    if not conta_bancaria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That conta_bancaria_id is not found. Please try another one.",
        )

    bobelo_bb_in_db = await boletos_bb_repo.register_new_boleto_bb(
        tenant=tenant_origin,
        convenio_bancario=convenio_bancario,
        conta_bancaria=conta_bancaria,
        new_boleto=new_boleto,
        token_bb_redis_repo=token_bb_redis_repo,
    )

    return bobelo_bb_in_db


@router.get(
    "",
    response_model=PageModel,
    name="contas-bancarias:get-all-contas-bancarias",
)
async def get_all_boletos_bb(
    boletos_bb_repo: BoletosBBRepository = Depends(get_repository(BoletosBBRepository)),
    tenant_origin: TenantInDB = Depends(get_tenant_by_api_key),
    current_page: int = 1,
    per_page: int = 10,
    data_emissao_gte: Optional[date] = None,
    data_emissao_lte: Optional[date] = None,
    data_vencimento_gte: Optional[date] = None,
    data_vencimento_lte: Optional[date] = None,
    valor_original_gte: Optional[condecimal()] = None,
    valor_original_lte: Optional[condecimal()] = None,
    nosso_numero: Optional[constr(min_length=20, max_length=20)] = None,
    seu_numero: Optional[conint()] = None,
    tipo_pessoa: Optional[PersonType] = None,
    cpf_cnpj: Optional[constr(min_length=11, max_length=19)] = None,
    nome: Optional[constr()] = None,
    sorts: Optional[str] = None,
) -> PageModel:
    filters = []
    if data_emissao_gte:
        filters.append(
            FilterModel(
                table="boletos_bb",
                field="data_emissao",
                alias_field="data_emissao_gte",
                operator="gte",
                value=data_emissao_gte,
            )
        )
    if data_emissao_lte:
        filters.append(
            FilterModel(
                table="boletos_bb",
                field="data_emissao",
                alias_field="data_emissao_lte",
                operator="lte",
                value=data_emissao_lte,
            )
        )
    if data_vencimento_gte:
        filters.append(
            FilterModel(
                table="boletos_bb",
                field="data_vencimento",
                alias_field="data_vencimento_gte",
                operator="gte",
                value=data_vencimento_gte,
            )
        )
    if data_vencimento_lte:
        filters.append(
            FilterModel(
                table="boletos_bb",
                field="data_vencimento",
                alias_field="data_vencimento_lte",
                operator="lte",
                value=data_vencimento_lte,
            )
        )
    if valor_original_gte:
        filters.append(
            FilterModel(
                table="boletos_bb",
                field="valor_original",
                alias_field="valor_original_gte",
                operator="gte",
                value=valor_original_gte,
            )
        )
    if valor_original_lte:
        filters.append(
            FilterModel(
                table="boletos_bb",
                field="valor_original",
                alias_field="valor_original_lte",
                operator="lte",
                value=valor_original_lte,
            )
        )
    if nosso_numero:
        filters.append(
            FilterModel(
                table="boletos_bb",
                field="numero_inscricao",
                alias_field="nosso_numero",
                operator="eq",
                value=nosso_numero,
            )
        )
    if seu_numero:
        filters.append(
            FilterModel(
                table="boletos_bb",
                field="numero_titulo_beneficiario",
                alias_field="seu_numero",
                operator="eq",
                value=seu_numero,
            )
        )
    if tipo_pessoa:
        filters.append(
            FilterModel(
                table="pagadores_bb",
                field="tipo_inscricao",
                alias_field="tipo_pessoa",
                operator="eq",
                value=tipo_pessoa,
            )
        )
    if cpf_cnpj:
        filters.append(
            FilterModel(
                table="pagadores_bb",
                field="numero_inscricao",
                alias_field="cpf_cnpj",
                operator="eq",
                value=validate_cpf_cnpj(cpf_cnpj),
            )
        )
    if nome:
        filters.append(
            FilterModel(
                table="pagadores_bb",
                field="nome",
                alias_field="nome",
                operator="ilike",
                value=f"%{nome}%",
            )
        )

    return await boletos_bb_repo.get_all_boletos_bb(
        tenant_id=tenant_origin.id, current_page=current_page, per_page=per_page, filters=filters, sorts=sorts
    )
