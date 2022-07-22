from typing import Optional
from pydantic import UUID4, condecimal, conint, constr
from app.schemas.bancos.conta_bancaria import ContaBancariaFull

from app.schemas.base import BaseSchema, DateTimeModelMixin, IDModelMixin, IDModelWithTenantMixin


class ConvenioBancarioBase(BaseSchema):
    conta_bancaria_id: UUID4
    numero_convenio: conint(ge=1000000, le=9999999)
    numero_carteira: conint(ge=10, le=99)
    numero_variacao_carteira: conint(ge=10, le=99)
    descricao_tipo_titulo: constr(min_length=2, max_length=2)
    numero_dias_limite_recebimento: conint()
    percentual_multa: Optional[condecimal(max_digits=2)]
    percentual_juros: Optional[condecimal(max_digits=2)]
    is_active: Optional[bool]


class ConvenioBancarioCreate(ConvenioBancarioBase):
    numero_dias_limite_recebimento: conint() = 0
    is_active: Optional[bool] = True


class ConvenioBancarioUpdate(ConvenioBancarioBase):
    conta_bancaria_id: Optional[UUID4] = None
    numero_convenio: Optional[conint(ge=1000000, le=9999999)] = None
    numero_carteira: Optional[conint(ge=10, le=99)] = None
    numero_variacao_carteira: Optional[conint(ge=10, le=99)] = None
    descricao_tipo_titulo: Optional[constr(min_length=2, max_length=2)] = None
    percentual_multa: Optional[condecimal(max_digits=2)] = None
    percentual_juros: Optional[condecimal(max_digits=2)] = None
    is_active: Optional[bool] = None


class ConvenioBancarioWithTenantCreate(ConvenioBancarioCreate):
    tenant_id: UUID4


class ConvenioBancarioInDB(DateTimeModelMixin, ConvenioBancarioBase, IDModelWithTenantMixin):
    class Config:
        orm_mode = True


class ConvenioBancarioInDBWithoutTenant(DateTimeModelMixin, ConvenioBancarioBase, IDModelMixin):
    class Config:
        orm_mode = True


class ConvenioBancarioFull(ConvenioBancarioBase, IDModelMixin):
    conta_bancaria: Optional[ContaBancariaFull]

    class Config:
        orm_mode = True


class ConvenioBancarioForList(ConvenioBancarioBase, IDModelMixin):
    nome_conta: str
    numero_conta: int
    numero_conta_dv: str
