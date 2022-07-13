import secrets
from typing import Optional
from pydantic import BaseModel, EmailStr, constr, validator

from app.schemas.enums import PersonType, StatesUF
from app.schemas.user import UserCreate
from .base import IDModelMixin, DateTimeModelMixin, BaseSchema
from app.util.validators import validate_cpf_cnpj, validate_phone_number


class TenantBase(BaseSchema):
    name: constr(min_length=3, max_length=140)
    brand: constr(min_length=3, max_length=140) = None
    type: PersonType
    email: EmailStr
    cpf_cnpj: constr(min_length=11, max_length=18)
    subdomain: constr(min_length=3, max_length=10)
    domain: constr(min_length=3, max_length=140)

    @validator("cpf_cnpj", pre=True)
    def cpf_cnpj_is_valid(cls, cpf_cnpj: str) -> str:
        return validate_cpf_cnpj(cpf_cnpj)


class TenantCreate(TenantBase):
    ie: Optional[constr(max_length=20)] = None
    cep: Optional[constr(max_length=9)] = None
    street: Optional[constr(max_length=140)] = None
    number: Optional[constr(max_length=10)] = None
    complement: Optional[constr(max_length=140)] = None
    neighborhood: Optional[constr(max_length=140)] = None
    city: Optional[constr(max_length=140)] = None
    state: Optional[StatesUF] = None
    phone: Optional[constr(max_length=15)] = None
    cell_phone: Optional[constr(max_length=15)] = None
    api_key: str = secrets.token_urlsafe(64)

    @validator("phone", pre=True)
    def phone_is_valid(cls, phone: str) -> str:
        return validate_phone_number(phone)

    @validator("cell_phone", pre=True)
    def cell_phone_is_valid(cls, cell_phone: str) -> str:
        return validate_phone_number(cell_phone)


class TenantWithUserCreate(TenantCreate):
    # username: constr(min_length=3, max_length=70)
    # password: constr(min_length=8, max_length=100)
    # password_confirmation: constr(min_length=8, max_length=100)
    admin_user: UserCreate


class TenantUpdate(BaseSchema):
    name: Optional[constr(min_length=3, max_length=140)]
    brand: Optional[constr(min_length=3, max_length=140)]
    type: Optional[PersonType]
    email: Optional[EmailStr]
    cpf_cnpj: Optional[constr(min_length=11, max_length=18)]
    ie: Optional[constr(max_length=20)]
    subdomain: Optional[constr(min_length=3, max_length=10)]
    domain: Optional[constr(min_length=3, max_length=140)]
    cep: Optional[constr(max_length=9)]
    street: Optional[constr(max_length=140)]
    number: Optional[constr(max_length=10)]
    complement: Optional[constr(max_length=140)]
    neighborhood: Optional[constr(max_length=140)]
    city: Optional[constr(max_length=140)]
    state: Optional[StatesUF]
    phone: Optional[constr(max_length=15)]
    cell_phone: Optional[constr(max_length=15)]
    is_active: Optional[bool] = True

    # @validator("cpf_cnpj", pre=True)
    # def cpf_cnpj_is_valid(cls, cpf_cnpj: str) -> str:
    #     return validate_cpf_cnpj(cpf_cnpj)

    @validator("phone", pre=True)
    def phone_is_valid(cls, phone: str) -> str:
        return validate_phone_number(phone)

    @validator("cell_phone", pre=True)
    def cell_phone_is_valid(cls, cell_phone: str) -> str:
        return validate_phone_number(cell_phone)


class Tenant(TenantCreate, IDModelMixin):
    is_active: Optional[bool] = False
    is_master: Optional[bool] = False
    email_verified: Optional[bool] = False


class TenantInDB(DateTimeModelMixin, Tenant):
    class Config:
        orm_mode = True


class TenantRedis(BaseModel):
    id: str
    name: str
    type: str
    cpf_cnpj: str
    email: str
    subdomain: str
    domain: str
    is_master: str
