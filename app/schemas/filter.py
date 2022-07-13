from typing import Any, Optional
from pydantic import BaseModel


class FilterModel(BaseModel):
    table: Optional[str] = None
    field: str
    alias_field: Optional[str] = None
    operator: str
    value: Any
