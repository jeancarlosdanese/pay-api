from pydantic.types import UUID4
from app.util.validators import validate_phone_number
from typing import List, Optional
from fastapi.param_functions import Form
from pydantic import EmailStr, constr, validator
from app.schemas.permission import Permission
from app.schemas.role import Role

from .base import BaseSchema, DateTimeModelMixin, IDModelMixin, IDModelWithTenantMixin


class UserBase(BaseSchema):
    full_name: constr(min_length=3, max_length=140)
    email: EmailStr
    username: constr(min_length=3, max_length=70)
    cell_phone: Optional[constr(max_length=15)] = None
    thumbnail: Optional[constr(max_length=140)] = None


class UserFilter(BaseSchema):
    full_name: Optional[constr(min_length=3, max_length=140)] = None
    email: Optional[EmailStr] = None
    username: Optional[constr(min_length=3, max_length=70)] = None  # noqa
    cell_phone: Optional[constr(max_length=15)] = None


class UserWithTenantCreate(UserBase):
    tenant_id: UUID4
    hashed_password: constr(min_length=8, max_length=100)


class UserCreate(UserBase):
    password: constr(min_length=8, max_length=100)
    password_confirmation: constr(min_length=8, max_length=100)

    @validator("cell_phone", pre=True)
    def cell_phone_is_valid(cls, cell_phone: str) -> str:
        return validate_phone_number(cell_phone)


class UserFullCreate(UserCreate):
    roles: Optional[List[UUID4]] = None
    permissions: Optional[List[UUID4]] = None


class UserUpdate(BaseSchema):
    full_name: Optional[constr(min_length=3, max_length=140)] = None
    email: Optional[EmailStr] = None
    username: Optional[constr(min_length=3, max_length=70)] = None
    cell_phone: Optional[constr(max_length=15)] = None
    is_active: Optional[bool] = None

    @validator("cell_phone", pre=True)
    def cell_phone_is_valid(cls, cell_phone: str) -> str:
        return validate_phone_number(cell_phone)


class UserForgotPassword(BaseSchema):
    def __init__(
        self,
        email: EmailStr = Form(...),
    ):
        self.email = email


class UserResetPassword(BaseSchema):
    password: constr(min_length=8, max_length=100)
    password_confirmation: constr(min_length=8, max_length=100)


class UserInDB(DateTimeModelMixin, UserBase, IDModelWithTenantMixin):
    hashed_password: Optional[str]
    email_verified: Optional[bool] = False
    is_active: Optional[bool] = False

    class Config:
        orm_mode = True


class UserFull(DateTimeModelMixin, UserBase, IDModelMixin):
    email_verified: Optional[bool] = False
    is_active: Optional[bool] = True
    roles: Optional[List[Role]] = []
    permissions: Optional[List[Permission]] = []
    extra_permissions: Optional[List[Permission]] = []


class UserPublic(DateTimeModelMixin, UserBase, IDModelMixin):
    email_verified: Optional[bool] = False
    is_active: Optional[bool] = None


class UserSummary(UserBase, IDModelMixin):
    pass
