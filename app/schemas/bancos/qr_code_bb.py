from typing import Optional
from pydantic import UUID4, constr

from app.schemas.base import BaseSchema, DateTimeModelMixin, IDModelMixin
from app.util.utils import camel_to_underscore, underscore_to_camel


class QrCode(BaseSchema):
    url: Optional[constr(max_length=140)]
    tx_id: Optional[constr(max_length=70)]
    emv: Optional[constr(max_length=254)]


class QrCodeBB(QrCode):
    class Config:
        alias_generator = underscore_to_camel


class QrCodeWithTenantCreate(QrCodeBB):
    tenant_id: Optional[UUID4]
    boleto_bb_id: Optional[UUID4]

    class Config:
        alias_generator = camel_to_underscore


class QrCodeFull(QrCode, IDModelMixin):
    pass


class QrCodeInDB(DateTimeModelMixin, QrCodeFull):
    pass
