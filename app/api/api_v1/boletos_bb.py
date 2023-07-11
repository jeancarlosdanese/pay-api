import httpx
from starlette.responses import StreamingResponse
from datetime import date
from typing import Any, Optional
from pydantic import condecimal, conint, constr
from app.api.dependencies.boletos_bb import get_boleto_bb_by_id_from_path, get_boleto_bb_by_seu_numero_from_path
from app.api.dependencies.database import get_repository
from fastapi import BackgroundTasks, Body, Depends, HTTPException, status
from app.api.dependencies.redis_database import get_redis_repository
from app.db.repositories.boletos_bb import BoletosBBRepository
from app.db.repositories.convenios_bancarios import ConveniosBancariosRepository
from app.db.repositories.contas_bancarias import ContasBancariasRepository
from app.db.repositories.token_bb_redis import TokenBBRedisRepository
from app.schemas.bancos.boleto import BoletoCreate
from app.schemas.bancos.boleto_bb import (
    AlteracaoData,
    BoletoBBAlteracao,
    BoletoBBBaixar,
    BoletoBBFull,
    BoletoBBInDB,
    BoletoBBNewVencimento,
    BoletoBBResponseDetails,
    BoletoBBResponseDetailsSnake,
)
from app.schemas.bancos.boleto_pdf import BeneficiarioBoleto, DadosBoletoBB, PagadorBoleto
from app.schemas.enums import PersonType
from app.schemas.filter import FilterModel
from app.schemas.page import PageModel

from app.schemas.tenant import TenantInDB
from fastapi.routing import APIRouter
from app.api.dependencies.auth import get_tenant_by_api_key
from app.services.boleto_bb_pdf import create_boleto_bb_pdf
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
        tenant_in_db=tenant_origin,
        convenio_bancario_in_db=convenio_bancario,
        conta_bancaria_in_db=conta_bancaria,
        new_boleto=new_boleto,
        token_bb_redis_repo=token_bb_redis_repo,
    )

    return bobelo_bb_in_db


@router.get(
    "",
    response_model=PageModel,
    name="boletos-bb:get-all-boletos-bb",
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


@router.get(
    "/{id}",
    response_model=BoletoBBFull,
    name="boletos-bb:get-boleto-bb-by-id",
)
async def get_boleto_bb_by_id(
    boleto_bb: BoletoBBFull = Depends(get_boleto_bb_by_id_from_path),
) -> BoletoBBFull:
    return boleto_bb


@router.get(
    "/{id}/consulta",
    response_model=BoletoBBResponseDetailsSnake,
    name="boletos-bb:get-boleto-bb-by-id-consulta",
)
async def get_boleto_bb_by_id_consulta(
    boleto_bb: BoletoBBFull = Depends(get_boleto_bb_by_id_from_path),
    token_bb_redis_repo: TokenBBRedisRepository = Depends(get_redis_repository(TokenBBRedisRepository)),
    boletos_bb_repo: BoletosBBRepository = Depends(get_repository(BoletosBBRepository)),
) -> BoletoBBResponseDetails:
    boleto_bb_full = BoletoBBFull(**boleto_bb)
    boleto_bb_response = await boletos_bb_repo.consultar_situacao_boleto_bb(
        id=boleto_bb_full.id, token_bb_redis_repo=token_bb_redis_repo
    )

    boleto_response = BoletoBBResponseDetailsSnake(**boleto_bb_response)

    return boleto_response


@router.get(
    "/{seu_numero}/seu-numero",
    response_model=BoletoBBResponseDetailsSnake,
    name="boletos-bb:get-boleto-bb-consulta-by-seu-numero",
)
async def get_boleto_bb_consulta_by_seu_numero(
    boleto_bb: BoletoBBFull = Depends(get_boleto_bb_by_seu_numero_from_path),
    token_bb_redis_repo: TokenBBRedisRepository = Depends(get_redis_repository(TokenBBRedisRepository)),
    boletos_bb_repo: BoletosBBRepository = Depends(get_repository(BoletosBBRepository)),
) -> BoletoBBResponseDetails:
    boleto_bb_full = BoletoBBFull(**boleto_bb)
    boleto_bb_response = await boletos_bb_repo.consultar_situacao_boleto_bb(
        id=boleto_bb_full.id, token_bb_redis_repo=token_bb_redis_repo
    )
    return BoletoBBResponseDetailsSnake(**boleto_bb_response)


@router.get("/{id}/boleto-bb-pdf")
async def download_pdf_order(
    background_tasks: BackgroundTasks,
    # tenant_origin: TenantInDB = Depends(get_tenant_by_api_key),
    boleto_bb: BoletoBBFull = Depends(get_boleto_bb_by_id_from_path),
    cpf_cnpj_senha: bool = False,
):
    boleto_bb = BoletoBBFull(**boleto_bb)
    boleto = DadosBoletoBB(
        carteira=boleto_bb.convenio.numero_carteira,
        data_documento=boleto_bb.data_emissao,
        data_processamento=boleto_bb.data_emissao,
        data_vencimento=boleto_bb.data_vencimento,
        numero_documento=boleto_bb.numero_titulo_beneficiario,
        nosso_numero=boleto_bb.numero,
        valor_original=boleto_bb.valor_original,
        valor_desconto=boleto_bb.valor_desconto,
        linha_digitavel=boleto_bb.linha_digitavel,
        codigo_barras=boleto_bb.codigo_barra_numerico,
        qr_code=boleto_bb.qr_code.emv,
        especie_documento=boleto_bb.descricao_tipo_titulo,
        numero_dias_limite_recebimento=boleto_bb.convenio.numero_dias_limite_recebimento,
        taxa_juros_mes=boleto_bb.convenio.percentual_juros,
        taxa_multa=boleto_bb.convenio.percentual_multa,
        mensagem_beneficiario=boleto_bb.mensagem_beneficiario,
        beneficiario=BeneficiarioBoleto(
            agencia=f"{boleto_bb.convenio.conta_bancaria.agencia}-{boleto_bb.convenio.conta_bancaria.agencia_dv}",
            conta=f"{boleto_bb.convenio.conta_bancaria.numero_conta}-{boleto_bb.convenio.conta_bancaria.numero_conta_dv}",  # noqa flake8(E501)
            nome=boleto_bb.beneficiario.nome,
            cpf_cnpj=boleto_bb.beneficiario.cpf_cnpj,
            cep=boleto_bb.beneficiario.cep,
            logradouro=boleto_bb.beneficiario.logradouro,
            bairro=boleto_bb.beneficiario.bairro,
            cidade=boleto_bb.beneficiario.cidade,
            uf=boleto_bb.beneficiario.uf,
        ),
        pagador=PagadorBoleto(
            nome=boleto_bb.pagador.nome,
            cpf_cnpj=boleto_bb.pagador.cpf_cnpj,
            cep=boleto_bb.pagador.cep,
            logradouro=boleto_bb.pagador.endereco,
            bairro=boleto_bb.pagador.bairro,
            cidade=boleto_bb.pagador.cidade,
            uf=boleto_bb.pagador.uf,
        ),
    )

    file_boleto_bb_pdf = create_boleto_bb_pdf(boleto=boleto, cpf_cnpj_senha=cpf_cnpj_senha)

    return StreamingResponse(file_boleto_bb_pdf, media_type="application/pdf", background=background_tasks)


@router.patch(
    "/{id}",
    response_model=Any,
    name="boletos-bb:update-vencimento-boleto-bb-by-id",
)
async def update_vencimento_boleto_bb_by_id(
    boleto_bb: BoletoBBInDB = Depends(get_boleto_bb_by_id_from_path),
    new_vencimento: BoletoBBNewVencimento = Body(..., embed=False),
    convenios_bancarios_repo: ConveniosBancariosRepository = Depends(get_repository(ConveniosBancariosRepository)),
    boletos_bb_repo: BoletosBBRepository = Depends(get_repository(BoletosBBRepository)),
    token_bb_redis_repo: TokenBBRedisRepository = Depends(get_redis_repository(TokenBBRedisRepository)),
) -> Any:
    boleto_bb = BoletoBBInDB(**boleto_bb)
    convenio_bancario = await convenios_bancarios_repo.get_convenio_bancario_by_id(
        tenant_id=boleto_bb.tenant_id, id=boleto_bb.convenio_bancario_id
    )

    boleto_bb_alteracao = BoletoBBAlteracao(
        numeroConvenio=convenio_bancario.numero_convenio,
        indicadorNovaDataVencimento="S",
        alteracaoData=AlteracaoData(
            novaDataVencimento=new_vencimento.data_vencimento_format,
        ),
    )

    boleto_bb = await boletos_bb_repo.update_vencimento_boleto_bb(
        id=boleto_bb.id,
        new_vencimento=new_vencimento,
        boleto_bb_alteracao=boleto_bb_alteracao,
        token_bb_redis_repo=token_bb_redis_repo,
    )

    print(boleto_bb_alteracao.dict(exclude_unset=True))

    return boleto_bb


@router.post(
    "/{id}/baixar",
    response_model=Any,
    name="boletos-bb:baixar-boleto-bb-by-id",
)
async def baixar_boleto_bb_by_id(
    boleto_bb: BoletoBBInDB = Depends(get_boleto_bb_by_id_from_path),
    convenios_bancarios_repo: ConveniosBancariosRepository = Depends(get_repository(ConveniosBancariosRepository)),
    boletos_bb_repo: BoletosBBRepository = Depends(get_repository(BoletosBBRepository)),
    token_bb_redis_repo: TokenBBRedisRepository = Depends(get_redis_repository(TokenBBRedisRepository)),
) -> Any:
    print("OOOOppppaaaaa!!!")
    boleto_bb = BoletoBBInDB(**boleto_bb)
    convenio_bancario = await convenios_bancarios_repo.get_convenio_bancario_by_id(
        tenant_id=boleto_bb.tenant_id, id=boleto_bb.convenio_bancario_id
    )

    boleto_bb_baixar = BoletoBBBaixar(numeroConvenio=convenio_bancario.numero_convenio)

    boleto_bb = await boletos_bb_repo.baixar_boleto_bb(
        id=boleto_bb.id,
        boleto_bb_baixar=boleto_bb_baixar,
        token_bb_redis_repo=token_bb_redis_repo,
    )

    return boleto_bb


# @router.get("/{id}/pdf-order-base-64")
# async def download_pdf_order_base_64(
#     order: OrderInDB = Depends(
#         get_order_by_id_from_path_by_permissions(
#             [
#                 "add_order",
#                 "edit_order",
#                 "financial_analysis",
#                 "edit_photos",
#                 "edit_inspection",
#                 "print_photos",
#                 "plotter_photos",
#                 "assemble_order",
#                 "pack_order",
#             ]
#         )
#     ),
#     persons_repo: PersonsRepository = Depends(get_repository(PersonsRepository)),
#     orders_repo: OrdersRepository = Depends(get_repository(OrdersRepository)),
# ):
#     pdf_order_filename = await orders_repo.get_pdf_order_by_order(
#         tenant_id=order.tenant_id, persons_repo=persons_repo, order=order
#     )

#     with open(f"{pdf_order_filename}", "rb") as spcfile:
#         encoded_string = base64.b64encode(spcfile.read())

#     return encoded_string
