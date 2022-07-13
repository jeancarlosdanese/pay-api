import datetime
import ssl
import aiohttp
from fastapi import status
from app.core.config import BB_API_URL
from app.core.exceptions.exceptions_customs import HttpExceptionBB
from app.db.repositories.token_bb_redis import TokenBBRedisRepository
from app.schemas.bancos.beneficiario_bb import (
    BeneficiarioFinalBB,
    BeneficiarioInDB,
    BeneficiarioWithTenantCreate,
)
from app.schemas.bancos.boleto import BoletoCreate
from app.schemas.bancos.boleto_bb import (
    BoletoBBCreate,
    BoletoBBFull,
    BoletoBBInDB,
    BoletoBBWithTenantCreate,
    DescontoBB,
    JurosMoraBB,
    MultaBB,
    RegistroBoletoBB,
)

from databases.core import Database
from app.db.repositories.base import BaseRepository
from app.schemas.bancos.conta_bancaria import ContaBancariaInDB
from app.schemas.bancos.convenio_bancario import ConvenioBancarioInDB
from app.schemas.bancos.pagador_bb import Pagador, PagadorBB, PagadorInDB, PagadorWithTenantCreate
from app.schemas.bancos.qr_code_bb import QrCodeInDB, QrCodeWithTenantCreate
from app.schemas.tenant import TenantInDB

from app.services import auth_service
from app.services import auth_service_bb

from app.util.utils_bb import get_numero_titulo_cliente


CREATE_PAGADOR_BB_QUERY = """
    INSERT INTO pagadores_bb (tenant_id, boleto_bb_id, tipo_inscricao, numero_inscricao, nome, \
        endereco, cep, cidade, bairro, uf, telefone)
    VALUES(:tenant_id, :boleto_bb_id, :tipo_inscricao, :numero_inscricao, :nome, \
        :endereco, :cep, :cidade, :bairro, :uf, :telefone)
    RETURNING
        id, tenant_id, boleto_bb_id, tipo_inscricao, numero_inscricao, nome, \
        endereco, cep, cidade, bairro, uf, telefone, created_at, updated_at;
"""


CREATE_BENFICIARIO_BB_QUERY = """
    INSERT INTO beneficiarios_bb (tenant_id, boleto_bb_id, agencia, conta_corrente, tipo_endereco, \
        logradouro, bairro, cidade, codigo_cidade, uf, cep, indicador_comprovacao)
    VALUES(:tenant_id, :boleto_bb_id, :agencia, :conta_corrente, :tipo_endereco, \
        :logradouro, :bairro, :cidade, :codigo_cidade, :uf, :cep, :indicador_comprovacao)
    RETURNING
        id, tenant_id, boleto_bb_id, agencia, conta_corrente, tipo_endereco, logradouro, \
            bairro, cidade, codigo_cidade, uf, cep, indicador_comprovacao, created_at, updated_at;
"""


CREATE_QR_CODE_BB_QUERY = """
    INSERT INTO qr_codes_bb (tenant_id, boleto_bb_id, url, tx_id, emv)
    VALUES(:tenant_id, :boleto_bb_id, :url, :tx_id, :emv)
    RETURNING
        id, tenant_id, boleto_bb_id, url, tx_id, emv, created_at, updated_at;
"""


CREATE_BOLETO_BB_QUERY = """
    INSERT INTO boletos_bb (tenant_id, convenio_bancario_id, numero_titulo_beneficiario, data_emissao, \
        data_vencimento, valor_original, valor_desconto, descricao_tipo_titulo, numero, codigo_cliente, \
            linha_digitavel, codigo_barra_numerico, numero_contrato_cobranca
        )
    VALUES(:tenant_id, :convenio_bancario_id, :numero_titulo_beneficiario, :data_emissao, \
        :data_vencimento, :valor_original, :valor_desconto, :descricao_tipo_titulo, :numero, :codigo_cliente, \
        :linha_digitavel, :codigo_barra_numerico, :numero_contrato_cobranca)
    RETURNING
        id, tenant_id, convenio_bancario_id, numero_titulo_beneficiario, data_emissao, data_vencimento, \
        valor_original, valor_desconto, descricao_tipo_titulo, numero, codigo_cliente, linha_digitavel, \
            codigo_barra_numerico, numero_contrato_cobranca, created_at, updated_at;
"""


GET_BOLETO_BB_BY_ID_QUERY = """
    SELECT id, tenant_id, convenio_bancario_id, numero_titulo_beneficiario, data_emissao, \
        data_vencimento, valor_original, valor_desconto, descricao_tipo_titulo, numero, codigo_cliente, \
            linha_digitavel, codigo_barra_numerico, numero_contrato_cobranca, created_at, updated_at
    FROM
        boletos_bb;
"""


UPDATE_BOLETO_BB_BY_ID_QUERY = """
    UPDATE boletos_bb
    SET
        convenio_bancario_id = :convenio_bancario_id,
        numero_titulo_beneficiario = :numero_titulo_beneficiario,
        data_emissao = :data_emissao,
        data_vencimento = :data_vencimento,
        valor_original = :valor_original,
        valor_desconto = :valor_desconto,
        descricao_tipo_titulo = :descricao_tipo_titulo,
        numero = :numero,
        codigo_cliente = :codigo_cliente,
        linha_digitavel = :linha_digitavel,
        codigo_barra_numerico = :codigo_barra_numerico,
        numero_contrato_cobranca = :numero_contrato_cobranca
    WHERE
        tenant_id = :tenant_id
        AND id = :id
    RETURNING
        id, tenant_id, convenio_bancario_id, numero_titulo_beneficiario, data_emissao, data_vencimento, \
        valor_original, valor_desconto, descricao_tipo_titulo, numero, codigo_cliente, linha_digitavel, \
            codigo_barra_numerico, numero_contrato_cobranca, created_at, updated_at;
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

    async def register_new_boleto_bb(
        self,
        *,
        tenant: TenantInDB,
        convenio_bancario: ConvenioBancarioInDB,
        conta_bancaria: ContaBancariaInDB,
        new_boleto: BoletoCreate,
        token_bb_redis_repo: TokenBBRedisRepository,
    ) -> BoletoBBInDB:
        async with self.db.transaction():
            create_pagador = Pagador(
                **new_boleto.pagador.dict(),
            )

            create_boleto = BoletoBBWithTenantCreate(
                tenant_id=convenio_bancario.tenant_id,
                **new_boleto.dict(exclude={"pagador"}),
                numero=get_numero_titulo_cliente(
                    numero_convenio=convenio_bancario.numero_convenio,
                    numero_titulo_beneficiario=new_boleto.numero_titulo_beneficiario,
                ),
            )

            boleto_bb_created = await self.db.fetch_one(query=CREATE_BOLETO_BB_QUERY, values=create_boleto.dict())
            boleto_in_bd = BoletoBBInDB(**boleto_bb_created)

            boleto_bb_create = BoletoBBCreate(
                numeroConvenio=convenio_bancario.numero_convenio,
                numeroCarteira=convenio_bancario.numero_carteira,
                numeroVariacaoCarteira=convenio_bancario.numero_variacao_carteira,
                numeroTituloBeneficiario=boleto_in_bd.numero_titulo_beneficiario,
                dataEmissao=boleto_in_bd.data_emissao,
                dataVencimento=boleto_in_bd.data_vencimento,
                valorOriginal=boleto_in_bd.valor_original,
                desconto=DescontoBB(
                    tipo=1, dataExpiracao=boleto_in_bd.data_vencimento, valor=boleto_in_bd.valor_desconto
                )
                if boleto_in_bd.valor_desconto > 0
                else None,
                pagador=PagadorBB(
                    tipoInscricao=create_pagador.tipo_inscricao,
                    numeroInscricao=create_pagador.numero_inscricao,
                    nome=create_pagador.nome,
                    endereco=create_pagador.endereco,
                    cep=create_pagador.cep,
                    cidade=create_pagador.cidade,
                    bairro=create_pagador.bairro,
                    uf=create_pagador.uf,
                    telefone=create_pagador.telefone,
                ),
                multa=MultaBB(data=boleto_in_bd.data_vencimento + datetime.timedelta(days=1)),
                jurosMora=JurosMoraBB(),
                numeroTituloCliente=get_numero_titulo_cliente(
                    numero_convenio=convenio_bancario.numero_convenio,
                    numero_titulo_beneficiario=new_boleto.numero_titulo_beneficiario,
                ),
                beneficiarioFinal=BeneficiarioFinalBB(
                    tipoInscricao=2,
                    numeroInscricao=int(tenant.cpf_cnpj.replace("-", "").replace("/", "").replace(".", "")),
                    nome=tenant.name,
                ),
            )

            token = await auth_service_bb.get_access_token_bb(
                client_id=conta_bancaria.client_id,
                client_secret=conta_bancaria.client_secret,
                gw_dev_app_key=conta_bancaria.developer_application_key,
                token_bb_redis_repo=token_bb_redis_repo,
            )

            headers = {
                "Authorization": f"Bearer {token.access_token}",
                "Content-Type": "application/json",
            }

            params = {
                "gw-dev-app-key": conta_bancaria.developer_application_key,
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(
                    url=f"{BB_API_URL}/boletos", params=params, ssl=ssl.SSLContext(), data=boleto_bb_create.json()
                ) as response:
                    result = await response.json()
                    if response.status != status.HTTP_200_OK:
                        raise HttpExceptionBB(status_code=response.status, content=result)

                    registeredBoletoBB = RegistroBoletoBB(**result)

                    create_pagador = PagadorWithTenantCreate(
                        **create_pagador.dict(),
                        tenant_id=boleto_in_bd.tenant_id,
                        boleto_bb_id=boleto_in_bd.id,
                    )
                    pagador_bb_created = await self.db.fetch_one(
                        query=CREATE_PAGADOR_BB_QUERY, values=create_pagador.dict()
                    )
                    pagador_bb_in_db = PagadorInDB(**pagador_bb_created)

                    create_beneficiario = BeneficiarioWithTenantCreate(
                        **registeredBoletoBB.beneficiario.dict(),
                        tenant_id=boleto_in_bd.tenant_id,
                        boleto_bb_id=boleto_in_bd.id,
                    )
                    beneficiario_bb_created = await self.db.fetch_one(
                        query=CREATE_BENFICIARIO_BB_QUERY, values=create_beneficiario.dict()
                    )
                    beneficiario_bb_in_db = BeneficiarioInDB(**beneficiario_bb_created)

                    create_qr_code = QrCodeWithTenantCreate(
                        **registeredBoletoBB.qrCode.dict(),
                        tenant_id=boleto_in_bd.tenant_id,
                        boleto_bb_id=boleto_in_bd.id,
                    )
                    qr_code_bb_created = await self.db.fetch_one(
                        query=CREATE_QR_CODE_BB_QUERY, values=create_qr_code.dict()
                    )
                    qr_code_bb_in_db = QrCodeInDB(**qr_code_bb_created)

                    boleto_in_bd.codigo_cliente = registeredBoletoBB.codigoCliente
                    boleto_in_bd.linha_digitavel = registeredBoletoBB.linhaDigitavel
                    boleto_in_bd.codigo_barra_numerico = registeredBoletoBB.codigoBarraNumerico
                    boleto_in_bd.numero_contrato_cobranca = registeredBoletoBB.numeroContratoCobranca

                    boleto_bb_created = await self.db.fetch_one(
                        query=UPDATE_BOLETO_BB_BY_ID_QUERY,
                        values=boleto_in_bd.dict(
                            exclude={"pagador", "beneficiario", "qr_code", "created_at", "updated_at"}
                        ),
                    )

                    boleto_bb_full = BoletoBBFull(
                        **boleto_bb_created,
                        pagador=pagador_bb_in_db.dict(),
                        beneficiario=beneficiario_bb_in_db.dict(),
                        qr_code=qr_code_bb_in_db.dict(),
                    )

                    return boleto_bb_full
