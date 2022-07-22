from fastapi import HTTPException, status
from pydantic.types import UUID4, List, Optional
from app.schemas.bancos.convenio_bancario import (
    ConvenioBancarioCreate,
    ConvenioBancarioForList,
    ConvenioBancarioInDB,
    ConvenioBancarioUpdate,
    ConvenioBancarioWithTenantCreate,
)

from databases.core import Database
from app.db.repositories.base import BaseRepository
from app.schemas.page import PageModel
from app.schemas.token import Token

from app.services import auth_service

from pypika import Query, Table, Tables, Parameter


CREATE_CONVENIO_BANCARIO_QUERY = """
    INSERT INTO convenios_bancarios (tenant_id, conta_bancaria_id, numero_convenio, numero_carteira, \
        numero_variacao_carteira, numero_dias_limite_recebimento, descricao_tipo_titulo, percentual_multa, \
            percentual_juros, is_active)
    VALUES(:tenant_id, :conta_bancaria_id, :numero_convenio, :numero_carteira, :numero_variacao_carteira, \
        :numero_dias_limite_recebimento, :descricao_tipo_titulo, :percentual_multa, :percentual_juros, :is_active)
    RETURNING
        id, tenant_id, conta_bancaria_id, numero_convenio, numero_carteira, numero_variacao_carteira, \
            numero_dias_limite_recebimento, descricao_tipo_titulo, percentual_multa, percentual_juros, \
                is_active, created_at, updated_at;
"""


GET_CONVENIO_BANCARIO_BY_ID_QUERY = """
    SELECT
        id,
        tenant_id,
        conta_bancaria_id,
        numero_convenio,
        numero_carteira,
        numero_variacao_carteira,
        numero_dias_limite_recebimento,
        descricao_tipo_titulo,
        percentual_multa,
        percentual_juros,
        is_active,
        created_at,
        updated_at
    FROM
        convenios_bancarios
    WHERE
        tenant_id = :tenant_id
        AND id = :id;
"""


UPDATE_CONVENIO_BANCARIO_BY_ID_QUERY = """
    UPDATE convenios_bancarios
    SET
        conta_bancaria_id = :conta_bancaria_id,
        numero_convenio = :numero_convenio,
        numero_carteira = :numero_carteira,
        numero_variacao_carteira = :numero_variacao_carteira,
        numero_dias_limite_recebimento = :numero_dias_limite_recebimento, 
        descricao_tipo_titulo = :descricao_tipo_titulo,
        percentual_multa = :percentual_multa,
        percentual_juros = :percentual_juros,
        is_active = :is_active
    WHERE
        tenant_id = :tenant_id
        AND id = :id
    RETURNING
        id, tenant_id, conta_bancaria_id, numero_convenio, numero_carteira, numero_variacao_carteira, \
            numero_dias_limite_recebimento, descricao_tipo_titulo, percentual_multa, percentual_juros, \
                is_active, created_at, updated_at;
"""


DELETE_CONVENIO_BANCARIO_BY_ID_QUERY = """
    DELETE
    FROM convenios_bancarios
    WHERE
        tenant_id = :tenant_id
        AND id = :id
    RETURNING id;
"""


class ConveniosBancariosRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.auth_service = auth_service

    async def register_new_back_account(
        self, *, user_token: Token, new_back_account: ConvenioBancarioCreate
    ) -> ConvenioBancarioInDB:
        create_convenio_bancario = ConvenioBancarioWithTenantCreate(
            **new_back_account.dict(),
            tenant_id=user_token.tenant_id,
        )

        back_account = await self.db.fetch_one(
            query=CREATE_CONVENIO_BANCARIO_QUERY, values=create_convenio_bancario.dict()
        )
        return ConvenioBancarioInDB(**back_account)

    async def get_all_convenios_bancarios(
        self,
        *,
        tenant_id: UUID4,
        current_page: int = 1,
        per_page: int = 10,
        filters: List[str],
        sorts: Optional[str],
    ) -> PageModel:
        select_query = await self.__get_orders_select_query()
        count_query = await self.__get_orders_count_query()

        convenios_bancarios = Table("convenios_bancarios")

        return await self.get_page_by_params(
            table=convenios_bancarios,
            select_query=select_query,
            count_query=count_query,
            tenant_id=tenant_id,
            filters=filters,
            sorts=sorts,
            current_page=current_page,
            per_page=per_page,
            type_schema=ConvenioBancarioForList,
        )

    async def get_convenio_bancario_by_id(self, *, tenant_id: UUID4, id: UUID4):
        back_account = await self.db.fetch_one(
            query=GET_CONVENIO_BANCARIO_BY_ID_QUERY, values={"tenant_id": tenant_id, "id": id}
        )

        if not back_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No convenio_bancario found with that id.",
            )
        return ConvenioBancarioInDB(**back_account)

    async def update_convenio_bancario_by_id(
        self, *, convenio_bancario: ConvenioBancarioInDB, convenio_bancario_update: ConvenioBancarioUpdate
    ) -> ConvenioBancarioInDB:
        convenio_bancario_update_params = convenio_bancario.copy(
            update=convenio_bancario_update.dict(exclude_unset=True)
        )
        convenio_bancario_updated = await self.db.fetch_one(
            query=UPDATE_CONVENIO_BANCARIO_BY_ID_QUERY,
            values=convenio_bancario_update_params.dict(exclude={"created_at", "updated_at"}),
        )

        return convenio_bancario_updated

    async def delete_convenio_bancario_by_id(self, *, tenant_id: UUID4, id: UUID4) -> UUID4:
        deleted_id = await self.db.execute(
            query=DELETE_CONVENIO_BANCARIO_BY_ID_QUERY, values={"tenant_id": tenant_id, "id": id}
        )

        return deleted_id

    async def __get_orders_count_query(self) -> Query:
        convenios_bancarios, contas_bancarias = Tables(
            "convenios_bancarios",
            "contas_bancarias",
        )

        count_query = (
            Query.from_(convenios_bancarios)
            .inner_join(contas_bancarias)
            .on(convenios_bancarios.conta_bancaria_id == contas_bancarias.id)
            .where(convenios_bancarios.tenant_id == Parameter(":tenant_id"))
        )

        return count_query

    async def __get_orders_select_query(self) -> Query:
        convenios_bancarios, contas_bancarias = Tables(
            "convenios_bancarios",
            "contas_bancarias",
        )
        select_query = (
            Query.from_(convenios_bancarios)
            .inner_join(contas_bancarias)
            .on(convenios_bancarios.conta_bancaria_id == contas_bancarias.id)
            .select(
                convenios_bancarios.id,
                convenios_bancarios.conta_bancaria_id,
                contas_bancarias.nome.as_("nome_conta"),
                contas_bancarias.numero_conta.as_("numero_conta"),
                contas_bancarias.numero_conta_dv.as_("numero_conta_dv"),
                convenios_bancarios.numero_convenio,
                convenios_bancarios.numero_carteira,
                convenios_bancarios.numero_variacao_carteira,
                convenios_bancarios.descricao_tipo_titulo,
                convenios_bancarios.numero_dias_limite_recebimento,
                convenios_bancarios.percentual_multa,
                convenios_bancarios.percentual_juros,
                convenios_bancarios.is_active,
                convenios_bancarios.created_at,
                convenios_bancarios.updated_at,
            )
            .where(convenios_bancarios.tenant_id == Parameter(":tenant_id"))
        )

        return select_query
