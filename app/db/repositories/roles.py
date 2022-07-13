from typing import List

from pydantic.types import UUID4
from app.schemas.permission import Permission

from app.schemas.role import RoleFull, RoleInDB
from .base import BaseRepository


GET_ALL_ROLES_QUERY = """
    SELECT id, slug, name, created_at, updated_at
    FROM roles;
"""


GET_ROLE_BY_ID_QUERY = """
    SELECT id, slug, name, created_at, updated_at
    FROM roles
    WHERE id = :id;
"""


GET_ROLE_BY_USER_ID_QUERY = """
    SELECT r.id, r.slug, r.name, r.created_at, r.updated_at
    FROM roles r
    INNER JOIN roles_users ru ON ru.role_id = r.id
    WHERE ru.user_id = :user_id;
"""


GET_ROLE_BY_SLUG_QUERY = """
    SELECT id, slug, name, created_at, updated_at
    FROM roles
    WHERE slug = :slug;
"""


GET_PERMISSIONS_BY_ROLE_ID_QUERY = """
    SELECT p.id, p.slug, p.name
    FROM permissions_roles pr
    INNER JOIN permissions p ON p.id = pr.permission_id
    WHERE
        pr.role_id = :role_id;
"""


class RolesRepository(BaseRepository):
    """
    All database actions associated with the Role resource
    """

    async def get_all_roles(self) -> List[RoleInDB]:
        roles = await self.db.fetch_all(query=GET_ALL_ROLES_QUERY)
        if not roles:
            return None
        return roles

    async def get_role_by_id(self, *, id: UUID4) -> RoleFull:
        role_in_db = await self.db.fetch_one(query=GET_ROLE_BY_ID_QUERY, values={"id": id})
        if not role_in_db:
            return None

        role = RoleInDB(**role_in_db).dict()
        role["permissions"] = await self.get_permissions_by_role_id(role_id=role["id"])
        return RoleFull(**role)

    async def get_user_by_slug(self, *, slug: str) -> RoleInDB:
        role = await self.db.fetch_one(query=GET_ROLE_BY_SLUG_QUERY, values={"slug": slug})
        if not role:
            return None
        return RoleInDB(**role)

    async def get_permissions_by_role_id(self, *, role_id: UUID4) -> List[Permission]:
        permissions = await self.db.fetch_all(query=GET_PERMISSIONS_BY_ROLE_ID_QUERY, values={"role_id": role_id})
        if not permissions:
            return None

        return permissions

    async def get_roles_by_user_id(self, *, user_id: UUID4) -> List[RoleFull]:
        roles_in_db = await self.db.fetch_all(query=GET_ROLE_BY_USER_ID_QUERY, values={"user_id": user_id})
        if not roles_in_db:
            return []

        roles: List[RoleFull] = []
        for role_id_db in roles_in_db:
            role = RoleInDB(**role_id_db).dict()
            role["permissions"] = await self.get_permissions_by_role_id(role_id=role["id"])
            role_full = RoleFull(**role)
            roles.append(role_full)
        return roles
