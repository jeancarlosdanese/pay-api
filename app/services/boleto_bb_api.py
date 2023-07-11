import base64
import datetime
import re
import ssl
import aiohttp

from fastapi import status
from app.core.config import BB_API_URL, BB_OAUTH_URL
from app.core.exceptions.exceptions_customs import HttpExceptionBB
from app.db.repositories.token_bb_redis import TokenBBRedisRepository
from app.schemas.bancos.beneficiario_bb import BeneficiarioFinalBB
from app.schemas.bancos.boleto_bb import (
    BoletoBBCreate,
    BoletoBBInDB,
    BoletoBBRequestDetails,
    BoletoBBResponseDetails,
    DescontoBB,
    JurosMoraBB,
    MultaBB,
    RegistroBoletoBB,
)
from app.schemas.bancos.conta_bancaria import ContaBancariaInDB
from app.schemas.bancos.convenio_bancario import ConvenioBancarioInDB
from app.schemas.bancos.pagador_bb import PagadorBB, PagadorInDB
from app.schemas.tenant import TenantInDB
from app.schemas.token_bb import TokenBB
from app.util.utils_bb import get_numero_titulo_cliente


class BoletoBBService:
    async def registra_boleto_bb(
        self,
        *,
        conta_bancaria_in_db: ContaBancariaInDB,
        convenio_bancario_in_db: ConvenioBancarioInDB,
        boleto_in_bd: BoletoBBInDB,
        pagador_bb_in_db: PagadorInDB,
        tenant_in_db: TenantInDB,
        token_bb_redis_repo: TokenBBRedisRepository,
    ) -> RegistroBoletoBB:
        boleto_bb_create = self.prepare_boleto_bb_to_create(
            convenio_bancario_in_db=convenio_bancario_in_db,
            boleto_in_bd=boleto_in_bd,
            pagador_bb_in_db=pagador_bb_in_db,
            tenant_in_db=tenant_in_db,
        )

        token = await self.get_access_token_bb(
            client_id=conta_bancaria_in_db.client_id,
            client_secret=conta_bancaria_in_db.client_secret,
            gw_dev_app_key=conta_bancaria_in_db.developer_application_key,
            token_bb_redis_repo=token_bb_redis_repo,
        )

        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "Content-Type": "application/json",
        }

        params = {
            "gw-dev-app-key": conta_bancaria_in_db.developer_application_key,
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                url=f"{BB_API_URL}/boletos", params=params, ssl=ssl.SSLContext(), data=boleto_bb_create.json()
            ) as response:
                result = await response.json()

                if response.status in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
                    return RegistroBoletoBB(**result)

                # Tratamento de erros (está retornando os erros da API do BB)
                raise HttpExceptionBB(status_code=response.status, content=result)

    def prepare_boleto_bb_to_create(
        self,
        *,
        convenio_bancario_in_db: ConvenioBancarioInDB,
        boleto_in_bd: BoletoBBInDB,
        pagador_bb_in_db: PagadorInDB,
        tenant_in_db: TenantInDB,
    ):
        boleto_bb_create = BoletoBBCreate(
            numeroConvenio=convenio_bancario_in_db.numero_convenio,
            numeroCarteira=convenio_bancario_in_db.numero_carteira,
            numeroVariacaoCarteira=convenio_bancario_in_db.numero_variacao_carteira,
            numeroTituloBeneficiario=boleto_in_bd.numero_titulo_beneficiario,
            dataEmissao=boleto_in_bd.data_emissao,
            dataVencimento=boleto_in_bd.data_vencimento,
            valorOriginal=boleto_in_bd.valor_original,
            numeroDiasLimiteRecebimento=convenio_bancario_in_db.numero_dias_limite_recebimento,
            campoUtilizacaoBeneficiario=boleto_in_bd.mensagem_beneficiario,
            desconto=DescontoBB(tipo=1, dataExpiracao=boleto_in_bd.data_vencimento, valor=boleto_in_bd.valor_desconto)
            if boleto_in_bd.valor_desconto > 0
            else None,
            pagador=PagadorBB(
                tipoInscricao=pagador_bb_in_db.tipo_inscricao,
                numeroInscricao=pagador_bb_in_db.cpf_cnpj,
                nome=pagador_bb_in_db.nome,
                endereco=pagador_bb_in_db.endereco,
                cep=pagador_bb_in_db.cep,
                cidade=pagador_bb_in_db.cidade,
                bairro=pagador_bb_in_db.bairro,
                uf=pagador_bb_in_db.uf,
                telefone=pagador_bb_in_db.telefone,
            ),
            multa=MultaBB(data=boleto_in_bd.data_vencimento + datetime.timedelta(days=1)),
            jurosMora=JurosMoraBB(),
            numeroTituloCliente=get_numero_titulo_cliente(
                numero_convenio=convenio_bancario_in_db.numero_convenio,
                numero_titulo_beneficiario=boleto_in_bd.numero_titulo_beneficiario,
            ),
            beneficiarioFinal=BeneficiarioFinalBB(
                tipoInscricao=2 if tenant_in_db.type.juridica else 1,
                numeroInscricao=int(re.sub(r"\D", "", tenant_in_db.cpf_cnpj)),
                nome=tenant_in_db.name,
            ),
        )

        return boleto_bb_create

    async def consultar_situacao_boleto_bb(
        self,
        *,
        boleto_bb_req: BoletoBBRequestDetails,
        token_bb_redis_repo: TokenBBRedisRepository,
    ) -> BoletoBBResponseDetails:
        token = await self.get_access_token_bb(
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
            "numeroConvenio": boleto_bb_req.numero_convenio,
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                url=f"{BB_API_URL}/boletos/{boleto_bb_req.numero}",
                params=params,
                ssl=ssl.SSLContext(),
            ) as response:
                result = await response.json()
                if response.status != status.HTTP_200_OK:
                    raise HttpExceptionBB(status_code=response.status, content=result)

                # boleto_bb_response = BoletoBBResponseDetails(**result)
                # print(boleto_bb_response.dict())
                return result

    async def get_access_token_bb(
        self,
        *,
        grant_type: str = "client_credentials",
        client_id: str,
        client_secret: str,
        gw_dev_app_key: str,
        token_bb_redis_repo: TokenBBRedisRepository,
    ) -> TokenBB:
        token = await token_bb_redis_repo.get_token_by_id(id=gw_dev_app_key)

        if token:
            return token

        # basic_encoded = base64.b64encode(bytes(f"{client_id}:{client_secret}", "utf-8"))
        basic_encoded = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
        headers = {
            "Authorization": f"Basic {basic_encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        params = {
            "gw-dev-app-key": gw_dev_app_key,
        }

        data = {"grant_type": grant_type, "client_id": client_id, "client_secret": client_secret}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                url=f"{BB_OAUTH_URL}/token", params=params, ssl=ssl.SSLContext(), data=data
            ) as response:
                if response.status in [status.HTTP_201_CREATED, status.HTTP_200_OK]:
                    result = await response.json()
                    token = TokenBB(id=gw_dev_app_key, **result)
                    await token_bb_redis_repo.set_token(token=token, expires_in=token.expires_in - 60)
                    return token
