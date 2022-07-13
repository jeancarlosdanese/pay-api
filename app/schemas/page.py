import math
from typing import List, TypeVar
from pydantic.main import BaseModel


DataT = TypeVar("DataT")


class Page(BaseModel):
    total: int = 0
    per_page: int = 10
    current_page: int = 1
    first_page: int = 1
    is_empty: bool = True
    last_page: int = 1
    has_next_page: bool = False
    has_previous_page: bool = False

    @classmethod
    def init(cls, current_page: int, total: int, per_page: int):
        total = total
        per_page = per_page
        current_page = current_page
        last_page = math.ceil(total / per_page) if per_page > 0 else 1

        return cls(
            current_page=current_page,
            total=total,
            per_page=per_page,
            # first_page=first_page,
            is_empty=True if not total or total == 0 else False,
            last_page=last_page,
            has_next_page=True if current_page < last_page else False,
            has_previous_page=True if current_page > 1 else False,
        )


class PageModel(BaseModel):
    rows: List = []
    page: Page = Page()


# class PageModel(GenericModel, Generic[DataT]):
#     rows: List[DataT] = []
#     page: Page = Page()
