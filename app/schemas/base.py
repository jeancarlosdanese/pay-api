from app.util.validators import datetime_format
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, validator

from pydantic.types import UUID4


class BaseSchema(BaseModel):
    pass


class DateTimeModelMixin(BaseModel):
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @validator("created_at", "updated_at", pre=True)
    def default_datetime(cls, value: datetime) -> datetime:
        return datetime_format(value=value)


class IDModelMixin(BaseModel):
    id: Optional[UUID4]


class IDModelWithTenantMixin(IDModelMixin):
    tenant_id: Optional[UUID4]
