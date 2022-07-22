from pydantic.types import UUID4, List, Optional
from app.schemas.bancos.conta_bancaria import (
    ContaBancariaCreate,
    ContaBancariaForList,
    ContaBancariaInDB,
    ContaBancariaUpdate,
    ContaBancariaWithTenantCreate,
)

from databases.core import Database
from app.db.repositories.base import BaseRepository
from app.schemas.page import PageModel
from app.schemas.token import Token

from app.services import auth_service

from pypika import Query, Table, Parameter


CREATE_BANK_ACCOUNT_QUERY = """
    INSERT INTO contas_bancarias (tenant_id, nome, banco_id, tipo, agencia, agencia_dv, numero_conta, numero_conta_dv, \
        client_id, client_secret, developer_application_key, is_active)
    VALUES(:tenant_id, :nome, :banco_id, :tipo, :agencia, :agencia_dv, :numero_conta, :numero_conta_dv, \
        :client_id, :client_secret, :developer_application_key, :is_active)
    RETURNING
        id, tenant_id, nome, banco_id, "tipo", agencia, agencia_dv, numero_conta, numero_conta_dv, \
            client_id, client_secret, developer_application_key, is_active, \
                created_at, updated_at;
"""


GET_BANK_ACCOUNT_BY_ID_QUERY = """
    SELECT id, nome, tenant_id, banco_id, tipo, agencia, agencia_dv, numero_conta, numero_conta_dv, \
        client_id, client_secret, developer_application_key, is_active, \
            created_at, updated_at
    FROM
        contas_bancarias
    WHERE
        tenant_id = :tenant_id
        AND id = :id;
"""


UPDATE_CONTA_BANCARIA_BY_ID_QUERY = """
    UPDATE contas_bancarias
    SET
        nome = :nome,
        banco_id = :banco_id,
        tipo = :tipo,
        agencia = :agencia,
        agencia_dv = :agencia_dv,
        numero_conta = :numero_conta,
        numero_conta_dv = :numero_conta_dv,
        client_id = :client_id,
        client_secret = :client_secret,
        developer_application_key = :developer_application_key,
        is_active = :is_active
    WHERE
        tenant_id = :tenant_id
        AND id = :id
    RETURNING id, tenant_id, nome, banco_id, "tipo", agencia, agencia_dv, numero_conta, numero_conta_dv, \
            client_id, client_secret, developer_application_key, is_active, created_at, updated_at;
"""


DELETE_CONTA_BANCARIA_BY_ID_QUERY = """
    DELETE
    FROM contas_bancarias
    WHERE
        tenant_id = :tenant_id
        AND id = :id
    RETURNING id;
"""


class ContasBancariasRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.auth_service = auth_service

    async def register_new_back_account(
        self, *, user_token: Token, new_back_account: ContaBancariaCreate
    ) -> ContaBancariaInDB:
        create_conta_bancaria = ContaBancariaWithTenantCreate(
            **new_back_account.dict(),
            tenant_id=user_token.tenant_id,
        )

        back_account = await self.db.fetch_one(query=CREATE_BANK_ACCOUNT_QUERY, values=create_conta_bancaria.dict())
        return ContaBancariaInDB(**back_account)

    async def get_all_contas_bancarias(
        self,
        *,
        tenant_id: UUID4,
        current_page: int = 1,
        per_page: int = 10,
        filters: List[str],
        sorts: Optional[str],
    ) -> PageModel:
        contas_bancarias = Table("contas_bancarias")
        select_query = (
            Query.from_(contas_bancarias)
            .select(
                contas_bancarias.id,
                contas_bancarias.tenant_id,
                contas_bancarias.nome,
                contas_bancarias.banco_id,
                contas_bancarias.tipo,
                contas_bancarias.agencia,
                contas_bancarias.agencia_dv,
                contas_bancarias.numero_conta,
                contas_bancarias.numero_conta_dv,
                contas_bancarias.client_id,
                contas_bancarias.client_secret,
                contas_bancarias.developer_application_key,
                contas_bancarias.is_active,
                contas_bancarias.created_at,
                contas_bancarias.updated_at,
            )
            .where(contas_bancarias.tenant_id == Parameter(":tenant_id"))
        )

        count_query = Query.from_(contas_bancarias).where(contas_bancarias.tenant_id == Parameter(":tenant_id"))

        return await self.get_page_by_params(
            table=contas_bancarias,
            select_query=select_query,
            count_query=count_query,
            tenant_id=tenant_id,
            filters=filters,
            sorts=sorts,
            current_page=current_page,
            per_page=per_page,
            type_schema=ContaBancariaForList,
        )

    async def get_conta_bancaria_by_id(self, *, tenant_id: UUID4, id: UUID4):
        conta_bancaria = await self.db.fetch_one(
            query=GET_BANK_ACCOUNT_BY_ID_QUERY, values={"tenant_id": tenant_id, "id": id}
        )

        if not conta_bancaria:
            return None

        return ContaBancariaInDB(**conta_bancaria)

    async def update_conta_bancaria_by_id(
        self, *, conta_bancaria: ContaBancariaInDB, conta_bancaria_update: ContaBancariaUpdate
    ) -> ContaBancariaInDB:
        conta_bancaria_update_params = conta_bancaria.copy(update=conta_bancaria_update.dict(exclude_unset=True))
        conta_bancaria_updated = await self.db.fetch_one(
            query=UPDATE_CONTA_BANCARIA_BY_ID_QUERY,
            values=conta_bancaria_update_params.dict(exclude={"created_at", "updated_at"}),
        )

        return conta_bancaria_updated

    async def delete_conta_bancaria_by_id(self, *, tenant_id: UUID4, id: UUID4) -> UUID4:
        deleted_id = await self.db.execute(
            query=DELETE_CONTA_BANCARIA_BY_ID_QUERY, values={"tenant_id": tenant_id, "id": id}
        )

        return deleted_id
