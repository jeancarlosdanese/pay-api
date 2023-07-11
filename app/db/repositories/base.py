import logging
import json
from databases import Database
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from pydantic import UUID4, BaseModel
from app.core.config import DEV_MODE
from app.schemas.page import Page, PageModel
from app.schemas.sort import SortModel
from app.schemas.filter import FilterModel
from pypika import PostgreSQLQuery as Query, Table, Field, Parameter, Order, functions as fn

logger = logging.getLogger("app")


class BaseRepository:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.logger = logger

    async def get_page_by_params(
        self,
        *,
        table: Table,
        select_query: Query,
        count_query: Query,
        tenant_id=UUID4,
        filters: List[FilterModel],
        sorts: str,
        current_page: int = 1,
        per_page: int = 20,
        type_schema: type,
    ) -> PageModel:
        values = {"tenant_id": tenant_id}

        if per_page > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="per_page must be less than 500.",
            )

        if filters and isinstance(filters, list):
            """filter_condition: Its a list, ie: [(key,operator,value)] operator list:
            eq for ==
            lt for <
            lte for <=
            gt for >
            gte for >=
            in for in_
            like for like
            """

            for clause in filters:
                param_str = clause.alias_field if clause.alias_field else clause.field
                if clause.operator != "is":
                    values[param_str] = clause.value

                if clause.table:
                    table = Table(clause.table)
                    field = Field(name=clause.field, table=table)
                else:
                    field = Field(clause.field)

                param = Parameter(f":{param_str}")
                operator = clause.operator

                if operator == "like":
                    count_query = count_query.where(field.like(param))
                    select_query = select_query.where(field.like(param))

                if operator == "ilike":
                    count_query = count_query.where(field.ilike(param))
                    select_query = select_query.where(field.ilike(param))

                elif operator == "eq":
                    count_query = count_query.where(field.eq(param))
                    select_query = select_query.where(field.eq(param))

                elif operator == "gt":
                    count_query = count_query.where(field.gt(param))
                    select_query = select_query.where(field.gt(param))

                elif operator == "gte":
                    count_query = count_query.where(field.gte(param))
                    select_query = select_query.where(field.gte(param))

                elif operator == "lt":
                    count_query = count_query.where(field.lt(param))
                    select_query = select_query.where(field.lt(param))

                elif operator == "lte":
                    count_query = count_query.where(field.lte(param))
                    select_query = select_query.where(field.lte(param))

                elif operator == "in":  # not tested
                    if isinstance(clause.value, list):
                        count_query = count_query.where(field.in_(param))
                        select_query = select_query.where(field.in_(param))
                    else:
                        count_query = count_query.where(field.in_(param.split(",")))
                        select_query = select_query.where(field.in_(param).split(","))

        count_query = count_query.select(fn.Count(table.id).as_("total"))

        # self.logger.warn(count_query)
        count_reg = await self.db.fetch_one(query=count_query.get_sql(), values=values)
        total = dict(count_reg)["total"]

        if total == 0:
            return PageModel()

        off_set = (current_page - 1) * per_page
        if off_set > total:
            off_set = 0
            current_page = 1

        if sorts:
            sorts_array = [SortModel(**dict(zip(["field", "order"], r.split(":")))) for r in sorts.split(",")]
            for row in sorts_array:
                select_query = select_query.orderby(Field(row.field), order=Order(row.order))

        select_query = select_query.limit(per_page).offset(off_set)

        # self.logger.warn(select_query)
        rows = await self.db.fetch_all(query=select_query.get_sql(), values=values)
        rows = [type_schema(**u) for u in rows]

        page = Page.init(total=total, per_page=per_page, current_page=current_page)
        return PageModel(rows=rows, page=page)

    def get_insert_query(self, *, table_name: str, obj: BaseModel) -> Query:
        obj: Dict = obj.dict()
        fields = obj.keys()
        parameters = []

        for field in fields:
            parameters.append(Parameter(f":{field}"))

        insert_query = Query.into(table_name).columns(tuple(fields)).insert(tuple(parameters)).returning("*")

        if DEV_MODE:
            self.logger.warn(insert_query)

        return insert_query

    def get_base_select_count_query(self, *, table_name: str) -> Query:
        table = Table(table_name)
        return Query.from_(table).select(fn.Count(table.id).as_("total"))

    def get_base_select_query(self, *, table_name: str, type_schema: BaseModel) -> Query:
        json_schema = json.loads(type_schema.schema_json())
        properties = json_schema["properties"]

        select_query = Query.from_(Table(table_name))
        for key in properties.keys():
            select_query = select_query.select(f"{key}")

        return select_query

    def get_select_query_by_id(self, *, table_name: str) -> Query:
        select_query = Query.from_(Table(table_name)).select("*").where(Field("id").eq(Parameter(f":{'id'}")))

        if DEV_MODE:
            self.logger.warn(select_query)

        return select_query

    def get_select_query_by_empresa_id_and_id(self, *, table_name: str) -> Query:
        select_query = (
            Query.from_(Table(table_name))
            .select("*")
            .where(Field("empresa_id").eq(Parameter(f":{'empresa_id'}")))
            .where(Field("id").eq(Parameter(f":{'id'}")))
        )

        if DEV_MODE:
            self.logger.warn(select_query)

        return select_query

    def get_update_query_by_id(self, *, table_name: str, obj: BaseModel) -> Query:
        table = Table(table_name)
        obj: Dict = obj.dict()
        keys = obj.keys()

        update_query = Query.update(table)
        for key in keys:
            if key not in ["id", "created_at", "updated_at"]:
                update_query = update_query.set(Field(key), Parameter(f":{key}"))

        update_query = update_query.where(Field("id").eq(Parameter(f":{'id'}")))
        update_query = update_query.returning("*")

        if DEV_MODE:
            self.logger.warn(update_query)

        return update_query

    def get_delete_query_by_id(self, *, table_name: str) -> Query:
        table = Table(table_name)

        delete_query = Query.from_(table).delete().where(Field("id").eq(Parameter(f":{'id'}"))).returning("id")

        if DEV_MODE:
            self.logger.warn(delete_query)

        return delete_query

    def get_delete_query_by_fields_without_return(
        self, *, table_name: str, fields_by_filter: Optional[List] = None
    ) -> Query:
        table = Table(table_name)

        delete_query = Query.from_(table).delete()

        for field in fields_by_filter:
            delete_query = delete_query.where(Field(field).eq(Parameter(f":{field}")))

        if DEV_MODE:
            self.logger.warn(delete_query)

        return delete_query
