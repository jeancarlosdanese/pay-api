import datetime
import ssl
from typing import Any, List, Optional
import aiohttp
from fastapi import HTTPException, status
from pydantic import UUID4
from pypika import Table, Tables, PostgreSQLQuery as Query, Parameter, Field
from app.core.config import BB_API_URL
from app.core.exceptions.exceptions_customs import HttpExceptionBB
from app.db.repositories.token_bb_redis import TokenBBRedisRepository
from app.schemas.bancos.beneficiario_bb import (
    BeneficiarioInDB,
    # BeneficiarioWithTenantCreate,
)
from app.schemas.bancos.boleto import BoletoCreate
from app.schemas.bancos.boleto_bb import (
    BoletoBBAlteracao,
    BoletoBBBaixar,
    BoletoBBForList,
    BoletoBBFull,
    BoletoBBInDB,
    BoletoBBNewVencimento,
    BoletoBBRequestDetails,
    BoletoBBResponseDetails,
    BoletoBBWithTenantCreate,
)

from databases.core import Database
from app.db.repositories.base import BaseRepository
from app.schemas.bancos.conta_bancaria import ContaBancariaInDB
from app.schemas.bancos.convenio_bancario import ConvenioBancarioInDB
from app.schemas.bancos.pagador_bb import Pagador, PagadorInDB, PagadorWithTenantCreate
from app.schemas.bancos.qr_code_bb import QrCodeInDB, QrCodeWithTenantCreate
from app.schemas.filter import FilterModel
from app.schemas.tenant import TenantInDB

from app.services import auth_service
from app.services import boleto_bb_service

from app.util.utils_bb import get_numero_titulo_cliente


CREATE_QR_CODE_BB_QUERY = """
    INSERT INTO qr_codes_bb (tenant_id, boleto_bb_id, url, tx_id, emv)
    VALUES(:tenant_id, :boleto_bb_id, :url, :tx_id, :emv)
    RETURNING
        id, tenant_id, boleto_bb_id, url, tx_id, emv, created_at, updated_at;
"""


GET_BOLETO_BB_BY_ID_QUERY = """
    SELECT id, tenant_id, convenio_bancario_id, pagador_bb_id, numero_titulo_beneficiario, data_emissao, \
        data_vencimento, data_recebimento, data_credito, data_baixa_automatico, valor_original, \
        valor_desconto, valor_pago_sacado, valor_credito_cedente, valor_desconto_utilizado, \
        valor_multa_recebido, valor_juros_recebido, descricao_tipo_titulo, numero, mensagem_beneficiario, \
        codigo_cliente, linha_digitavel, codigo_barra_numerico, numero_contrato_cobranca, created_at, updated_at
    FROM
        boletos_bb
    WHERE
        tenant_id = :tenant_id
        AND id = :id;
"""


GET_BOLETO_BB_REQUEST_DETAIL_BY_ID_QUERY = """
    SELECT b.id, numero, numero_convenio, client_id, client_secret, developer_application_key
    FROM
        boletos_bb b
        INNER JOIN convenios_bancarios cv ON b.convenio_bancario_id = cv.id
        INNER JOIN contas_bancarias cc ON cv.conta_bancaria_id = cc.id
    WHERE
        b.id = :id;
"""


GET_CONVENIO_BANCARIO_BB_BY_ID_QUERY = """
    SELECT id, tenant_id, conta_bancaria_id, numero_convenio, numero_carteira, numero_variacao_carteira, \
        numero_dias_limite_recebimento, descricao_tipo_titulo, percentual_multa, percentual_juros, \
            is_active, created_at, updated_at
    FROM
        convenios_bancarios
    WHERE
        tenant_id = :tenant_id
        AND id = :id;
"""


GET_CONTA_BANCARIA_BB_BY_ID_QUERY = """
    SELECT id, nome, tenant_id, banco_id, tipo, agencia, agencia_dv, numero_conta, numero_conta_dv, \
        client_id, client_secret, developer_application_key, is_active, created_at, updated_at
    FROM
        contas_bancarias
    WHERE
        tenant_id = :tenant_id
        AND id = :id;
"""


GET_PAGADOR_BB_BY_BOLETO_BB_ID_QUERY = """
    SELECT id, tenant_id, tipo_inscricao, cpf_cnpj, nome, \
        endereco, cep, cidade, bairro, uf, telefone, created_at, updated_at
    FROM
        pagadores_bb
    WHERE
        tenant_id = :tenant_id
        AND id = :id;
"""


GET_QR_CODE_BB_BY_BOLETO_BB_ID_QUERY = """
    SELECT id, tenant_id, boleto_bb_id, url, tx_id, emv, created_at, updated_at
    FROM
        qr_codes_bb
    WHERE
        tenant_id = :tenant_id
        AND boleto_bb_id = :boleto_bb_id;
"""


DELETE_BOLETO_BB_BY_ID_QUERY = """
    DELETE
    FROM boletos_bb
    WHERE
        tenant_id = :tenant_id
        AND id = :id
    RETURNING id;
"""


class BoletosBBRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.auth_service = auth_service
        self.boleto_bb_service = boleto_bb_service
        self.tablename = "boletos_bb"

        # Definir a tabela pagadores_bb
        self.table_pagadores_bb = Table("pagadores_bb")

        # Define a tabela e suas colunas
        self.table_boletos_bb = Table("boletos_bb")

    async def register_new_boleto_bb(
        self,
        *,
        tenant_in_db: TenantInDB,
        convenio_bancario_in_db: ConvenioBancarioInDB,
        conta_bancaria_in_db: ContaBancariaInDB,
        new_boleto: BoletoCreate,
        token_bb_redis_repo: TokenBBRedisRepository,
    ) -> BoletoBBInDB:
        async with self.db.transaction():
            create_pagador = Pagador(
                **new_boleto.pagador.dict(),
            )

            # busca pagador com "cpf_cnpj", "cep", "endereco", "telefone" iguais
            pagador_bb_created = await self.db.fetch_one(
                query=self.__get_select_pagadores_bb_query().get_sql(),
                values={
                    "tenant_id": tenant_in_db.id,
                    "cpf_cnpj": create_pagador.cpf_cnpj,
                    "cep": create_pagador.cep,
                    "endereco": create_pagador.endereco,
                    "telefone": create_pagador.telefone,
                },
            )

            # Se não existe pagador, cria um.
            if not pagador_bb_created:
                create_pagador = PagadorWithTenantCreate(
                    **create_pagador.dict(),
                    tenant_id=tenant_in_db.id,
                    # boleto_bb_id=boleto_in_bd.id,
                )

                pagador_bb_created = await self.db.fetch_one(
                    query=self.__get_create_pagador_bb_query().get_sql(), values=create_pagador.dict()
                )

            pagador_bb_in_db = PagadorInDB(**pagador_bb_created)

            create_boleto = BoletoBBWithTenantCreate(
                tenant_id=convenio_bancario_in_db.tenant_id,
                pagador_bb_id=pagador_bb_in_db.id,
                **new_boleto.dict(
                    exclude={"pagador"},
                ),
                numero=get_numero_titulo_cliente(
                    numero_convenio=convenio_bancario_in_db.numero_convenio,
                    numero_titulo_beneficiario=new_boleto.numero_titulo_beneficiario,
                ),
                data_baixa_automatico=new_boleto.data_vencimento
                + datetime.timedelta(days=convenio_bancario_in_db.numero_dias_limite_recebimento),
            )

            boleto_bb_created = await self.db.fetch_one(
                query=self.__get_create_boleto_bb_query().get_sql(), values=create_boleto.dict()
            )
            boleto_in_bd = BoletoBBInDB(**boleto_bb_created)

        if not boleto_in_bd:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro indeterminado")

        async with self.db.transaction():
            registeredBoletoBB = await self.boleto_bb_service.registra_boleto_bb(
                conta_bancaria_in_db=conta_bancaria_in_db,
                convenio_bancario_in_db=convenio_bancario_in_db,
                boleto_in_bd=boleto_in_bd,
                pagador_bb_in_db=pagador_bb_in_db,
                tenant_in_db=tenant_in_db,
                token_bb_redis_repo=token_bb_redis_repo,
            )

            boleto_in_bd.codigo_cliente = registeredBoletoBB.codigoCliente
            boleto_in_bd.linha_digitavel = registeredBoletoBB.linhaDigitavel
            boleto_in_bd.codigo_barra_numerico = registeredBoletoBB.codigoBarraNumerico
            boleto_in_bd.numero_contrato_cobranca = registeredBoletoBB.numeroContratoCobranca

            boleto_bb_updated = await self.db.fetch_one(
                query=self.__get_update_boleto_bb_query().get_sql(),
                values=boleto_in_bd.dict(exclude={"pagador", "beneficiario", "qr_code", "created_at", "updated_at"}),
            )

            create_qr_code = QrCodeWithTenantCreate(
                **registeredBoletoBB.qrCode.dict(),
                tenant_id=boleto_in_bd.tenant_id,
                boleto_bb_id=boleto_in_bd.id,
            )
            qr_code_bb_created = await self.db.fetch_one(query=CREATE_QR_CODE_BB_QUERY, values=create_qr_code.dict())
            qr_code_bb_in_db = QrCodeInDB(**qr_code_bb_created)

            boleto_bb_full = BoletoBBFull(
                **boleto_bb_updated,
                convenio=convenio_bancario_in_db.dict(),
                pagador=pagador_bb_in_db.dict(),
                # beneficiario=beneficiario_bb_in_db.dict(),
                qr_code=qr_code_bb_in_db.dict(),
            )

            return boleto_bb_full

    async def get_all_boletos_bb(
        self,
        *,
        tenant_id: UUID4,
        current_page: int = 1,
        per_page: int = 10,
        filters: List[FilterModel],
        sorts: Optional[str] = None,
    ) -> BoletoBBInDB:
        select_query = await self.__get_boletos_bb_select_query()
        count_query = await self.__get_boletos_bb_count_query()

        boletos_bb = Table("boletos_bb")

        return await self.get_page_by_params(
            table=boletos_bb,
            select_query=select_query,
            count_query=count_query,
            tenant_id=tenant_id,
            filters=filters,
            sorts=sorts,
            current_page=current_page,
            per_page=per_page,
            type_schema=BoletoBBForList,
        )

    async def __get_boletos_bb_count_query(self) -> Query:
        boletos_bb, pagadores_bb = Tables(
            "boletos_bb",
            "pagadores_bb",
        )

        count_query = (
            Query.from_(boletos_bb)
            .left_join(pagadores_bb)
            .on(pagadores_bb.id == boletos_bb.pagador_bb_id)
            .where(boletos_bb.tenant_id == Parameter(":tenant_id"))
        )

        return count_query

    async def __get_boletos_bb_select_query(self) -> Query:
        boletos_bb, pagadores_bb = Tables(
            "boletos_bb",
            "pagadores_bb",
        )

        select_query = (
            Query.from_(boletos_bb)
            .left_join(pagadores_bb)
            .on(pagadores_bb.id == boletos_bb.pagador_bb_id)
            .select(
                boletos_bb.id,
                boletos_bb.tenant_id,
                boletos_bb.convenio_bancario_id,
                boletos_bb.numero_titulo_beneficiario,
                boletos_bb.data_emissao,
                boletos_bb.data_vencimento,
                boletos_bb.valor_original,
                boletos_bb.valor_desconto,
                boletos_bb.descricao_tipo_titulo,
                boletos_bb.numero,
                boletos_bb.codigo_cliente,
                boletos_bb.linha_digitavel,
                boletos_bb.codigo_barra_numerico,
                boletos_bb.numero_contrato_cobranca,
                boletos_bb.created_at,
                boletos_bb.updated_at,
                pagadores_bb.tipo_inscricao.as_("tipo_pessoa"),
                pagadores_bb.cpf_cnpj.as_("cpf_cnpj"),
                pagadores_bb.nome.as_("nome"),
                pagadores_bb.telefone.as_("telefone"),
            )
            .where(boletos_bb.tenant_id == Parameter(":tenant_id"))
        )

        return select_query

    async def get_boleto_bb_by_id(self, *, tenant: TenantInDB, id: UUID4) -> BoletoBBFull:
        boleto_bb = await self.db.fetch_one(query=GET_BOLETO_BB_BY_ID_QUERY, values={"tenant_id": tenant.id, "id": id})

        if not boleto_bb:
            return None

        return await self.__get_full_boleto_bb_by_tenant_in_db_and_boleto_bb_in_db(
            tenant=tenant, boleto_bb_in_db=boleto_bb
        )

    async def get_boleto_bb_by_seu_numero(self, *, tenant: TenantInDB, seu_numero: int) -> BoletoBBFull:
        print(self.__get_boleto_bb_by_seu_numero_query().get_sql())
        boleto_bb = await self.db.fetch_one(
            query=self.__get_boleto_bb_by_seu_numero_query().get_sql(),
            values={"tenant_id": tenant.id, "numero_titulo_beneficiario": seu_numero},
        )

        if not boleto_bb:
            return None

        return await self.__get_full_boleto_bb_by_tenant_in_db_and_boleto_bb_in_db(
            tenant=tenant, boleto_bb_in_db=boleto_bb
        )

    async def __get_full_boleto_bb_by_tenant_in_db_and_boleto_bb_in_db(
        self,
        *,
        tenant: TenantInDB,
        boleto_bb_in_db: BoletoBBInDB,
    ) -> BoletoBBFull:
        boleto_bb_in_db = BoletoBBInDB(**boleto_bb_in_db)

        convenio_bancario_bb = await self.db.fetch_one(
            query=GET_CONVENIO_BANCARIO_BB_BY_ID_QUERY,
            values={"tenant_id": tenant.id, "id": boleto_bb_in_db.convenio_bancario_id},
        )
        convenio_bancario_bb_in_db = ConvenioBancarioInDB(**convenio_bancario_bb)

        conta_bancaria_bb = await self.db.fetch_one(
            query=GET_CONTA_BANCARIA_BB_BY_ID_QUERY,
            values={"tenant_id": tenant.id, "id": convenio_bancario_bb_in_db.conta_bancaria_id},
        )
        conta_bancaria_bb_in_db = ContaBancariaInDB(**conta_bancaria_bb)

        pagador_bb = await self.db.fetch_one(
            query=GET_PAGADOR_BB_BY_BOLETO_BB_ID_QUERY,
            values={"tenant_id": tenant.id, "id": boleto_bb_in_db.pagador_bb_id},
        )
        if pagador_bb:
            pagador_bb_in_db = PagadorInDB(**pagador_bb)

        # beneficiario_bb = await self.db.fetch_one(
        #     query=GET_BENEFICIARIO_BB_BY_BOLETO_BB_ID_QUERY,
        #     values={"tenant_id": tenant.id, "boleto_bb_id": boleto_bb_in_db.id},
        # )
        # if beneficiario_bb:
        #     beneficiario_bb_in_db = BeneficiarioInDB(**beneficiario_bb)
        beneficiario_bb_in_db = BeneficiarioInDB(
            id=tenant.id,
            nome=tenant.name,
            cpf_cnpj=tenant.cpf_cnpj,
            agencia=f"{conta_bancaria_bb_in_db.agencia}-{conta_bancaria_bb_in_db.agencia_dv}",
            conta_corrente=f"{conta_bancaria_bb_in_db.numero_conta}-{conta_bancaria_bb_in_db.numero_conta_dv}",
            tipo_endereco=tenant.type,
            logradouro=f"{tenant.street}{f', {tenant.number}' if tenant.number else ''}",
            bairro=tenant.neighborhood,
            cidade=tenant.city,
            uf=tenant.state,
            cep=tenant.cep,
        )

        qr_code_bb = await self.db.fetch_one(
            query=GET_QR_CODE_BB_BY_BOLETO_BB_ID_QUERY,
            values={"tenant_id": tenant.id, "boleto_bb_id": boleto_bb_in_db.id},
        )
        if qr_code_bb:
            qr_code_bb_in_db = QrCodeInDB(**qr_code_bb)

        if not boleto_bb_in_db:
            return None

        boleto_bb_json = {
            **boleto_bb_in_db.dict(),
            "convenio": {
                **convenio_bancario_bb_in_db.dict(),
                "conta_bancaria": conta_bancaria_bb_in_db.dict(
                    exclude={"client_id", "client_secret", "developer_application_key", "is_active"}
                ),
            },
        }

        if pagador_bb:
            boleto_bb_json["pagador"] = pagador_bb_in_db.dict()

        # if beneficiario_bb_in_db:
        boleto_bb_json["beneficiario"] = {
            **beneficiario_bb_in_db.dict(),
            # "nome": tenant.name,
            # "cpf_cnpj": tenant.cpf_cnpj,
        }

        if qr_code_bb:
            boleto_bb_json["qr_code"] = qr_code_bb_in_db.dict()

        return boleto_bb_json

    async def consultar_situacao_boleto_bb(
        self,
        *,
        id: UUID4,
        token_bb_redis_repo: TokenBBRedisRepository,
    ) -> BoletoBBResponseDetails:
        boleto_bb_req_in_db = await self.db.fetch_one(query=GET_BOLETO_BB_REQUEST_DETAIL_BY_ID_QUERY, values={"id": id})
        boleto_bb_req = BoletoBBRequestDetails(**boleto_bb_req_in_db)

        boleto_bb_response = await self.boleto_bb_service.consultar_situacao_boleto_bb(
            boleto_bb_req=boleto_bb_req,
            token_bb_redis_repo=token_bb_redis_repo,
        )

        return boleto_bb_response

    async def update_vencimento_boleto_bb(
        self,
        *,
        id: UUID4,
        new_vencimento: BoletoBBNewVencimento,
        boleto_bb_alteracao: BoletoBBAlteracao,
        token_bb_redis_repo: TokenBBRedisRepository,
    ) -> Any:
        async with self.db.transaction():
            boleto_bb_req_in_db = await self.db.fetch_one(
                query=GET_BOLETO_BB_REQUEST_DETAIL_BY_ID_QUERY, values={"id": id}
            )
            # update_query = self.get_update_query_by_id(table_name="boletos_bb", obj=boleto_bb_alteracao)
            # print(update_query)

            boleto_bb_req = BoletoBBRequestDetails(**boleto_bb_req_in_db)

            token = await self.boleto_bb_service.get_access_token_bb(
                client_id=boleto_bb_req.client_id,
                client_secret=boleto_bb_req.client_secret,
                gw_dev_app_key=boleto_bb_req.developer_application_key,
                token_bb_redis_repo=token_bb_redis_repo,
            )

            headers = {
                "Authorization": f"Bearer {token.access_token}",
                "Content-Type": "application/json",
            }

            params = {
                "gw-dev-app-key": boleto_bb_req.developer_application_key,
            }

            query_update = self.__get_update_data_vencimento_query_by_id(id=id)
            boleto_bb_in_db = await self.db.fetch_one(
                query=query_update.get_sql(),
                values={"id": id, "data_vencimento": new_vencimento.data_vencimento},
            )

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.patch(
                    url=f"{BB_API_URL}/boletos/{boleto_bb_req.numero}",
                    params=params,
                    ssl=ssl.SSLContext(),
                    data=boleto_bb_alteracao.json(),
                ) as response:
                    result = await response.json()
                    print(f"Status code: {response.status}")
                    if response.status != status.HTTP_200_OK:
                        raise HttpExceptionBB(status_code=response.status, content=result)

                    return boleto_bb_in_db

    async def baixar_boleto_bb(
        self,
        *,
        id: UUID4,
        boleto_bb_baixar: BoletoBBBaixar,
        token_bb_redis_repo: TokenBBRedisRepository,
    ) -> Any:
        async with self.db.transaction():
            boleto_bb_req_in_db = await self.db.fetch_one(
                query=GET_BOLETO_BB_REQUEST_DETAIL_BY_ID_QUERY, values={"id": id}
            )

            boleto_bb_req = BoletoBBRequestDetails(**boleto_bb_req_in_db)

            token = await self.boleto_bb_service.get_access_token_bb(
                client_id=boleto_bb_req.client_id,
                client_secret=boleto_bb_req.client_secret,
                gw_dev_app_key=boleto_bb_req.developer_application_key,
                token_bb_redis_repo=token_bb_redis_repo,
            )

            headers = {
                "Authorization": f"Bearer {token.access_token}",
                "Content-Type": "application/json",
            }

            params = {
                "gw-dev-app-key": boleto_bb_req.developer_application_key,
            }

            query_update = self.__get_update_data_hora_baixa_query_by_id(id=id)
            boleto_bb_in_db = await self.db.fetch_one(
                query=query_update.get_sql(),
                values={"id": id, "data_hora_baixa": datetime.datetime.now()},
            )

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(
                    url=f"{BB_API_URL}/boletos/{boleto_bb_req.numero}/baixar",
                    params=params,
                    ssl=ssl.SSLContext(),
                    data=boleto_bb_baixar.json(),
                ) as response:
                    result = await response.json()

                    if response.status != status.HTTP_200_OK:
                        return result

                    return boleto_bb_in_db

    async def delete_boleto_bb_by_id(self, *, tenant_id: UUID4, id: UUID4) -> UUID4:
        deleted_id = await self.db.execute(
            query=DELETE_BOLETO_BB_BY_ID_QUERY, values={"tenant_id": tenant_id, "id": id}
        )

        return deleted_id

    def __get_update_data_vencimento_query_by_id(self, *, id: UUID4) -> str:
        boletos_bb_table = Table(self.tablename)
        update_query = Query.update(boletos_bb_table)
        update_query = update_query.set(Field("data_vencimento"), Parameter(":data_vencimento"))
        update_query = update_query.where(Field("id").eq(Parameter(":id")))
        update_query = update_query.returning("*")

        return update_query

    def __get_update_data_hora_baixa_query_by_id(self, *, id: UUID4) -> str:
        boletos_bb_table = Table(self.tablename)
        update_query = Query.update(boletos_bb_table)
        update_query = update_query.set(Field("data_hora_baixa"), Parameter(":data_hora_baixa"))
        update_query = update_query.where(Field("id").eq(Parameter(":id")))
        update_query = update_query.returning("*")

        return update_query

    def __get_create_boleto_bb_query(self):
        # Constrói a consulta
        query = (
            Query.into(self.table_boletos_bb)
            .columns(
                self.table_boletos_bb.tenant_id,
                self.table_boletos_bb.convenio_bancario_id,
                self.table_boletos_bb.pagador_bb_id,
                self.table_boletos_bb.numero_titulo_beneficiario,
                self.table_boletos_bb.data_emissao,
                self.table_boletos_bb.data_vencimento,
                self.table_boletos_bb.data_baixa_automatico,
                self.table_boletos_bb.valor_original,
                self.table_boletos_bb.valor_desconto,
                self.table_boletos_bb.descricao_tipo_titulo,
                self.table_boletos_bb.numero,
                self.table_boletos_bb.mensagem_beneficiario,
                self.table_boletos_bb.codigo_cliente,
                self.table_boletos_bb.linha_digitavel,
                self.table_boletos_bb.codigo_barra_numerico,
                self.table_boletos_bb.numero_contrato_cobranca,
            )
            .insert(
                Parameter(":tenant_id"),
                Parameter(":convenio_bancario_id"),
                Parameter(":pagador_bb_id"),
                Parameter(":numero_titulo_beneficiario"),
                Parameter(":data_emissao"),
                Parameter(":data_vencimento"),
                Parameter(":data_baixa_automatico"),
                Parameter(":valor_original"),
                Parameter(":valor_desconto"),
                Parameter(":descricao_tipo_titulo"),
                Parameter(":numero"),
                Parameter(":mensagem_beneficiario"),
                Parameter(":codigo_cliente"),
                Parameter(":linha_digitavel"),
                Parameter(":codigo_barra_numerico"),
                Parameter(":numero_contrato_cobranca"),
            )
            .returning(
                self.table_boletos_bb.id,
                self.table_boletos_bb.tenant_id,
                self.table_boletos_bb.convenio_bancario_id,
                self.table_boletos_bb.pagador_bb_id,
                self.table_boletos_bb.numero_titulo_beneficiario,
                self.table_boletos_bb.data_emissao,
                self.table_boletos_bb.data_vencimento,
                self.table_boletos_bb.data_recebimento,
                self.table_boletos_bb.data_credito,
                self.table_boletos_bb.data_baixa_automatico,
                self.table_boletos_bb.valor_original,
                self.table_boletos_bb.valor_desconto,
                self.table_boletos_bb.valor_pago_sacado,
                self.table_boletos_bb.valor_credito_cedente,
                self.table_boletos_bb.valor_desconto_utilizado,
                self.table_boletos_bb.valor_multa_recebido,
                self.table_boletos_bb.valor_juros_recebido,
                self.table_boletos_bb.descricao_tipo_titulo,
                self.table_boletos_bb.numero,
                self.table_boletos_bb.mensagem_beneficiario,
                self.table_boletos_bb.codigo_cliente,
                self.table_boletos_bb.linha_digitavel,
                self.table_boletos_bb.codigo_barra_numerico,
                self.table_boletos_bb.numero_contrato_cobranca,
                self.table_boletos_bb.created_at,
                self.table_boletos_bb.updated_at,
            )
        )

        # return pypika query
        return query

    def __get_update_boleto_bb_query(self):
        # Constrói a consulta
        query = (
            Query.update(self.table_boletos_bb)
            .set(self.table_boletos_bb.convenio_bancario_id, Parameter(":convenio_bancario_id"))
            .set(self.table_boletos_bb.numero_titulo_beneficiario, Parameter(":numero_titulo_beneficiario"))
            .set(self.table_boletos_bb.pagador_bb_id, Parameter(":pagador_bb_id"))
            .set(self.table_boletos_bb.data_emissao, Parameter(":data_emissao"))
            .set(self.table_boletos_bb.data_vencimento, Parameter(":data_vencimento"))
            .set(self.table_boletos_bb.data_recebimento, Parameter(":data_recebimento"))
            .set(self.table_boletos_bb.data_credito, Parameter(":data_credito"))
            .set(self.table_boletos_bb.data_baixa_automatico, Parameter(":data_baixa_automatico"))
            .set(self.table_boletos_bb.valor_original, Parameter(":valor_original"))
            .set(self.table_boletos_bb.valor_desconto, Parameter(":valor_desconto"))
            .set(self.table_boletos_bb.valor_pago_sacado, Parameter(":valor_pago_sacado"))
            .set(self.table_boletos_bb.valor_credito_cedente, Parameter(":valor_credito_cedente"))
            .set(self.table_boletos_bb.valor_desconto_utilizado, Parameter(":valor_desconto_utilizado"))
            .set(self.table_boletos_bb.valor_multa_recebido, Parameter(":valor_multa_recebido"))
            .set(self.table_boletos_bb.valor_juros_recebido, Parameter(":valor_juros_recebido"))
            .set(self.table_boletos_bb.descricao_tipo_titulo, Parameter(":descricao_tipo_titulo"))
            .set(self.table_boletos_bb.numero, Parameter(":numero"))
            .set(self.table_boletos_bb.mensagem_beneficiario, Parameter(":mensagem_beneficiario"))
            .set(self.table_boletos_bb.codigo_cliente, Parameter(":codigo_cliente"))
            .set(self.table_boletos_bb.linha_digitavel, Parameter(":linha_digitavel"))
            .set(self.table_boletos_bb.codigo_barra_numerico, Parameter(":codigo_barra_numerico"))
            .set(self.table_boletos_bb.numero_contrato_cobranca, Parameter(":numero_contrato_cobranca"))
            .where(
                (self.table_boletos_bb.tenant_id == Parameter(":tenant_id"))
                & (self.table_boletos_bb.id == Parameter(":id"))
            )
            .returning(
                self.table_boletos_bb.id,
                self.table_boletos_bb.tenant_id,
                self.table_boletos_bb.convenio_bancario_id,
                self.table_boletos_bb.numero_titulo_beneficiario,
                self.table_boletos_bb.data_emissao,
                self.table_boletos_bb.data_vencimento,
                self.table_boletos_bb.data_recebimento,
                self.table_boletos_bb.data_credito,
                self.table_boletos_bb.data_baixa_automatico,
                self.table_boletos_bb.valor_original,
                self.table_boletos_bb.valor_desconto,
                self.table_boletos_bb.valor_pago_sacado,
                self.table_boletos_bb.valor_credito_cedente,
                self.table_boletos_bb.valor_desconto_utilizado,
                self.table_boletos_bb.valor_multa_recebido,
                self.table_boletos_bb.valor_juros_recebido,
                self.table_boletos_bb.descricao_tipo_titulo,
                self.table_boletos_bb.numero,
                self.table_boletos_bb.mensagem_beneficiario,
                self.table_boletos_bb.codigo_cliente,
                self.table_boletos_bb.linha_digitavel,
                self.table_boletos_bb.codigo_barra_numerico,
                self.table_boletos_bb.numero_contrato_cobranca,
                self.table_boletos_bb.created_at,
                self.table_boletos_bb.updated_at,
            )
        )

        return query

    def __get_create_pagador_bb_query(self):
        # Constrói a consulta
        query = (
            Query.into(self.table_pagadores_bb)
            .columns(
                self.table_pagadores_bb.tenant_id,
                self.table_pagadores_bb.tipo_inscricao,
                self.table_pagadores_bb.cpf_cnpj,
                self.table_pagadores_bb.nome,
                self.table_pagadores_bb.endereco,
                self.table_pagadores_bb.cep,
                self.table_pagadores_bb.cidade,
                self.table_pagadores_bb.bairro,
                self.table_pagadores_bb.uf,
                self.table_pagadores_bb.telefone,
            )
            .insert(
                Parameter(":tenant_id"),
                Parameter(":tipo_inscricao"),
                Parameter(":cpf_cnpj"),
                Parameter(":nome"),
                Parameter(":endereco"),
                Parameter(":cep"),
                Parameter(":cidade"),
                Parameter(":bairro"),
                Parameter(":uf"),
                Parameter(":telefone"),
            )
            .returning(
                self.table_pagadores_bb.id,
                self.table_pagadores_bb.tenant_id,
                self.table_pagadores_bb.tipo_inscricao,
                self.table_pagadores_bb.cpf_cnpj,
                self.table_pagadores_bb.nome,
                self.table_pagadores_bb.endereco,
                self.table_pagadores_bb.cep,
                self.table_pagadores_bb.cidade,
                self.table_pagadores_bb.bairro,
                self.table_pagadores_bb.uf,
                self.table_pagadores_bb.telefone,
                self.table_pagadores_bb.created_at,
                self.table_pagadores_bb.updated_at,
            )
        )

        # retorna query
        return query

    def __get_select_pagadores_bb_query(self):
        # Construir a consulta
        query = (
            Query()
            .select(
                self.table_pagadores_bb.id,
                self.table_pagadores_bb.tenant_id,
                self.table_pagadores_bb.tipo_inscricao,
                self.table_pagadores_bb.cpf_cnpj,
                self.table_pagadores_bb.nome,
                self.table_pagadores_bb.endereco,
                self.table_pagadores_bb.cep,
                self.table_pagadores_bb.cidade,
                self.table_pagadores_bb.bairro,
                self.table_pagadores_bb.uf,
                self.table_pagadores_bb.telefone,
                self.table_pagadores_bb.created_at,
                self.table_pagadores_bb.updated_at,
            )
            .from_(self.table_pagadores_bb)
            .where(
                (self.table_pagadores_bb.tenant_id == Parameter(":tenant_id"))
                & (self.table_pagadores_bb.cpf_cnpj == Parameter(":cpf_cnpj"))
                & (self.table_pagadores_bb.cep == Parameter(":cep"))
                & (self.table_pagadores_bb.endereco == Parameter(":endereco"))
                & (self.table_pagadores_bb.telefone == Parameter(":telefone"))
            )
        )

        return query

    def __get_boleto_bb_by_seu_numero_query(self):
        query = (
            Query.from_(self.table_boletos_bb)
            .select(
                self.table_boletos_bb.id,
                self.table_boletos_bb.tenant_id,
                self.table_boletos_bb.convenio_bancario_id,
                self.table_boletos_bb.pagador_bb_id,
                self.table_boletos_bb.numero_titulo_beneficiario,
                self.table_boletos_bb.data_emissao,
                self.table_boletos_bb.data_vencimento,
                self.table_boletos_bb.data_recebimento,
                self.table_boletos_bb.data_credito,
                self.table_boletos_bb.data_baixa_automatico,
                self.table_boletos_bb.valor_original,
                self.table_boletos_bb.valor_desconto,
                self.table_boletos_bb.valor_pago_sacado,
                self.table_boletos_bb.valor_credito_cedente,
                self.table_boletos_bb.valor_desconto_utilizado,
                self.table_boletos_bb.valor_multa_recebido,
                self.table_boletos_bb.valor_juros_recebido,
                self.table_boletos_bb.descricao_tipo_titulo,
                self.table_boletos_bb.numero,
                self.table_boletos_bb.mensagem_beneficiario,
                self.table_boletos_bb.codigo_cliente,
                self.table_boletos_bb.linha_digitavel,
                self.table_boletos_bb.codigo_barra_numerico,
                self.table_boletos_bb.numero_contrato_cobranca,
                self.table_boletos_bb.created_at,
                self.table_boletos_bb.updated_at,
            )
            .where(
                (self.table_boletos_bb.tenant_id == Parameter(":tenant_id"))
                & (self.table_boletos_bb.numero_titulo_beneficiario == Parameter(":numero_titulo_beneficiario"))
            )
        )

        return query
