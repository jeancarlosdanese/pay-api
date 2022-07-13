from typing import Optional
from pydantic import UUID4, constr, conint
from app.schemas.enums import ContaBancariaType

from app.schemas.base import BaseSchema, DateTimeModelMixin, IDModelMixin, IDModelWithTenantMixin


class ContaBancariaBase(BaseSchema):
    nome: constr(min_length=3, max_length=140)
    banco_id: conint()
    tipo: ContaBancariaType
    agencia: conint()
    agencia_dv: conint()
    numero_conta: conint()
    numero_conta_dv: constr(min_length=1, max_length=1)
    client_id: Optional[constr(min_length=1, max_length=170)] = None
    client_secret: Optional[constr(min_length=1, max_length=254)] = None
    developer_application_key: Optional[constr(min_length=1, max_length=70)] = None
    is_active: Optional[bool]


class ContaBancariaCreate(ContaBancariaBase):
    is_active: Optional[bool] = True


class ContaBancariaUpdate(ContaBancariaBase):
    nome: Optional[constr(min_length=3, max_length=140)] = None
    banco_id: Optional[conint()] = None
    tipo: Optional[ContaBancariaType] = None
    agencia: Optional[conint()] = None
    agencia_dv: Optional[conint()] = None
    numero_conta: Optional[conint()] = None
    numero_conta_dv: Optional[constr(min_length=1, max_length=1)] = None
    client_id: Optional[constr(min_length=1, max_length=170)] = None
    client_secret: Optional[constr(min_length=1, max_length=254)] = None
    developer_application_key: Optional[constr(min_length=1, max_length=70)] = None
    is_active: Optional[bool] = None


class ContaBancariaWithTenantCreate(ContaBancariaCreate):
    tenant_id: UUID4


class ContaBancariaInDB(DateTimeModelMixin, ContaBancariaBase, IDModelWithTenantMixin):
    class Config:
        orm_mode = True


class ContaBancariaInDBWithoutTenant(DateTimeModelMixin, ContaBancariaBase, IDModelMixin):
    class Config:
        orm_mode = True


class ContaBancariaFull(DateTimeModelMixin, ContaBancariaBase, IDModelMixin):
    class Config:
        orm_mode = True


class ContaBancariaForList(ContaBancariaBase, IDModelMixin):
    pass
