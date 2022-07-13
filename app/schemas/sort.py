from typing import Optional
from pydantic import BaseModel, validator
from fastapi import HTTPException, status


class SortModel(BaseModel):
    field: str
    order: Optional[str] = "ASC"

    @validator("order", pre=True)
    def work_phone_is_valid(cls, order: str) -> str:
        order = order.upper()
        if order not in ["ASC", "DESC"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="sorts order is not a valid value.",
            )
        return order
