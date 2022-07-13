from pydantic.types import UUID4
from app.schemas.permission import Permission
from datetime import datetime
from typing import List, Optional
from pydantic import constr
from pydantic.main import BaseModel

from .base import BaseSchema, DateTimeModelMixin, IDModelMixin


class RoleBase(BaseSchema):
    slug: constr(min_length=3, max_length=32, regex="^[a-zA-Z0-9_]+$")  # noqa
    name: constr(min_length=3, max_length=70)


class RoleInDB(DateTimeModelMixin, RoleBase, IDModelMixin):
    pass


class RoleFull(RoleInDB):
    permissions: Optional[List[Permission]] = None


class RoleUserBase(BaseSchema):
    role_id: UUID4
    user_id: UUID4


class RolesAddToUser(BaseSchema):
    roles: List[UUID4]


class RolesDeleteOfUser(RolesAddToUser):
    pass


class RoleUser(BaseModel):
    id: Optional[UUID4] = None
    role_id: Optional[UUID4] = None
    slug: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RoleUserInDB(DateTimeModelMixin, RoleUserBase, IDModelMixin):
    class Config:
        orm_mode = True


class Role(RoleBase, IDModelMixin):
    pass
