import logging
from databases import Database
from typing import List
from fastapi import HTTPException, status
from pydantic import UUID4
from app.schemas.page import Page, PageModel
from app.schemas.sort import SortModel
from app.schemas.filter import FilterModel
from pypika import Query, Table, Field, Parameter, Order, functions as fn

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

    # async def get_page_by_params(
    #     self,
    #     *,
    #     table: Table,
    #     select_query: Query,
    #     count_query: Query,
    #     current_user=UserInDB,
    #     filters: List[str],
    #     sorts: str,
    #     current_page: int = 1,
    #     per_page: int = 20,
    #     type_schema: type,
    # ) -> PageModel:
    #     values = {"tenant_id": current_user.tenant_id}

    #     if per_page > 500:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="per_page must be less than 500.",
    #         )

    #     if filters:
    #         """filter_condition: Its a list, ie: [(key,operator,value)] operator list:
    #         eq for ==
    #         lt for <
    #         lte for <=
    #         gt for >
    #         gte for >=
    #         in for in_
    #         like for like
    #         """
    #         for clause in filters:
    #             key, operator, value = clause
    #             fields = key.split(" as ")
    #             if len(fields) > 1:
    #                 field = fields[0]
    #                 param = fields[1]
    #             else:
    #                 field = key
    #                 param = key

    #             values[param] = value

    #             if operator == "like":
    #                 count_query = count_query.where(Field(field).ilike(Parameter(f":{param}")))
    #                 select_query = select_query.where(Field(field).ilike(Parameter(f":{param}")))

    #             elif operator == "eq":
    #                 count_query = count_query.where(Field(field).eq(Parameter(f":{param}")))
    #                 select_query = select_query.where(Field(field).eq(Parameter(f":{param}")))

    #             elif operator == "gt":  # not tested
    #                 count_query = count_query.where(Field(field).gt(Parameter(f":{param}")))
    #                 select_query = select_query.where(Field(field).gt(Parameter(f":{param}")))

    #             elif operator == "gte":  # not tested
    #                 count_query = count_query.where(Field(field).gte(Parameter(f":{param}")))
    #                 select_query = select_query.where(Field(field).gte(Parameter(f":{param}")))

    #             elif operator == "lte":  # not tested
    #                 count_query = count_query.where(Field(field).lte(Parameter(f":{param}")))
    #                 select_query = select_query.where(Field(field).lte(Parameter(f":{param}")))

    #             elif operator == "in":  # not tested
    #                 if isinstance(value, list):
    #                     count_query = count_query.where(Field(field).in_(Parameter(f":{param}")))
    #                     select_query = select_query.where(Field(field).in_(Parameter(f":{param}")))
    #                 else:
    #                     count_query = count_query.where(Field(field).in_(Parameter(f":{param}").split(",")))
    #                     select_query = select_query.where(Field(field).in_(Parameter(f":{param}").split(",")))

    #     count_query = count_query.select(fn.Count(table.id).as_("total"))

    #     # self.logger.warn(count_query)
    #     # self.logger.warn(values)
    #     count_reg = await self.db.fetch_one(query=count_query.get_sql(), values=values)
    #     total = dict(count_reg)["total"]

    #     if total == 0:
    #         return PageModel()

    #     off_set = (current_page - 1) * per_page
    #     if off_set > total:
    #         off_set = 0
    #         current_page = 1

    #     if sorts:
    #         sorts_array = [SortModel(**dict(zip(["field", "order"], r.split(":")))) for r in sorts.split(",")]
    #         for row in sorts_array:
    #             select_query = select_query.orderby(Field(row.field), order=Order(row.order))

    #     select_query = select_query.limit(per_page).offset(off_set)

    #     rows = await self.db.fetch_all(query=select_query.get_sql(), values=values)
    #     rows = [type_schema(**u) for u in rows]

    #     page = Page.init(total=total, per_page=per_page, current_page=current_page)
    #     return PageModel(rows=rows, page=page)
