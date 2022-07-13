from typing import List

from pydantic.types import UUID4

from app.schemas.permission import PermissionInDB
from .base import BaseRepository


GET_ALL_PERMISSIONS_QUERY = """
    SELECT id, slug, name, created_at, updated_at
    FROM permissions;
"""


GET_PERMISSION_BY_ID_QUERY = """
    SELECT id, slug, name, created_at, updated_at
    FROM permissions
    WHERE id = :id;
"""


GET_PERMISSION_BY_USER_ID_QUERY = """
    SELECT p.id, p.slug, p.name, p.created_at, p.updated_at
    FROM permissions p
    INNER JOIN permissions_users pu ON pu.permission_id = p.id
    WHERE pu.user_id = :user_id;
"""


GET_PERMISSION_BY_SLUG_QUERY = """
    SELECT id, slug, name, created_at, updated_at
    FROM permissions
    WHERE slug = :slug;
"""


class PermissionsRepository(BaseRepository):
    """
    All database actions associated with the Permission resource
    """

    async def get_all_permissions(self) -> List[PermissionInDB]:
        permissions = await self.db.fetch_all(query=GET_ALL_PERMISSIONS_QUERY)
        if not permissions:
            return None
        return permissions

    async def get_permission_by_id(self, *, id: UUID4) -> PermissionInDB:
        permission = await self.db.fetch_one(query=GET_PERMISSION_BY_ID_QUERY, values={"id": id})
        if not permission:
            return None

        return permission

    async def get_permission_by_slug(self, *, slug: str) -> PermissionInDB:
        permission = await self.db.fetch_one(query=GET_PERMISSION_BY_SLUG_QUERY, values={"slug": slug})
        if not permission:
            return None
        return PermissionInDB(**permission)

    async def get_permissions_by_user_id(self, *, user_id: UUID4) -> PermissionInDB:
        permissions = await self.db.fetch_all(query=GET_PERMISSION_BY_USER_ID_QUERY, values={"user_id": user_id})
        if not permissions:
            return []

        return permissions
