from datetime import datetime
from typing import List, Optional
from pydantic import constr
from pydantic.main import BaseModel
from pydantic.types import UUID4

from .base import BaseSchema, DateTimeModelMixin, IDModelMixin


class PermissionBase(BaseSchema):
    slug: constr(min_length=3, max_length=32, regex="^[a-zA-Z0-9_]+$")  # noqa
    name: constr(min_length=3, max_length=70)  # noqa


class PermissionInDB(DateTimeModelMixin, PermissionBase, IDModelMixin):
    pass


class PermissionUserBase(BaseSchema):
    permission_id: UUID4
    user_id: UUID4


class PermissionsAddToUser(BaseSchema):
    permissions: List[UUID4]


class PermissionsDeleteOfUser(PermissionsAddToUser):
    pass


class PermissionUser(BaseModel):
    id: Optional[UUID4] = None
    permission_id: Optional[UUID4] = None
    user_id: Optional[UUID4] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PermissionUserInDB(IDModelMixin, DateTimeModelMixin, PermissionUserBase):
    class Config:
        orm_mode = True


class Permission(PermissionBase, IDModelMixin):
    pass
