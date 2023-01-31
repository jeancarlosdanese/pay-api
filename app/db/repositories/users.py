import secrets
import aiofiles
import boto3

from app.schemas.page import PageModel
from app.schemas.token import Token
from typing import List, Optional
from databases.core import Database
from pydantic import EmailStr, UUID4
from fastapi import HTTPException, status, UploadFile

from app.core.config import S3_BUCKET, S3_EXPIRES_IN
from app.db.repositories.base import BaseRepository
from app.schemas.permission import Permission, PermissionUserInDB
from app.schemas.role import Role, RoleUser
from app.schemas.user import (
    UserCreate,
    UserFull,
    UserInDB,
    UserPublic,
    UserSummary,
    UserUpdate,
    UserWithTenantCreate,
)
from app.services import auth_service
from pypika import Query, Table, Parameter

s3 = boto3.client("s3")


GET_USER_BY_EMAIL_QUERY = """
    SELECT id, tenant_id, full_name, username, email, hashed_password, email_verified, cell_phone, thumbnail, \
        is_active, created_at, updated_at
    FROM users
    WHERE
        email = :email;
"""


GET_USER_BY_TENANT_ID_AND_EMAIL_QUERY = """
    SELECT id, tenant_id, full_name, username, email, hashed_password, email_verified, cell_phone, thumbnail, \
        is_active, created_at, updated_at
    FROM users
    WHERE
        tenant_id = :tenant_id
        AND email = :email;
"""


GET_USER_BY_USERNAME_QUERY = """
    SELECT id, tenant_id, full_name, username, email, hashed_password, email_verified, cell_phone, thumbnail, \
        is_active, created_at, updated_at
    FROM users
    WHERE
        username = :username;
"""


GET_USER_BY_TENANT_ID_AND_USERNAME_QUERY = """
    SELECT id, tenant_id, full_name, username, email, hashed_password, email_verified, cell_phone, thumbnail, \
        is_active, created_at, updated_at
    FROM users
    WHERE
        tenant_id = :tenant_id
        AND username = :username;
"""


GET_USER_BY_ID_QUERY = """
    SELECT id, tenant_id, full_name, username, email, hashed_password, email_verified, cell_phone, thumbnail, \
        is_active, created_at, updated_at
    FROM users
    WHERE
        tenant_id = :tenant_id
        AND id = :id;
"""


GET_USERS_BY_TENANT_ID_QUERY = """
    SELECT id, tenant_id, full_name, username, email, hashed_password, email_verified, cell_phone, thumbnail, \
        is_active, created_at, updated_at
    FROM users
    WHERE
        tenant_id = :tenant_id;
"""


REGISTER_NEW_USER_QUERY = """
    INSERT INTO users (tenant_id, full_name, username, email, hashed_password, cell_phone, thumbnail)
    VALUES (:tenant_id, :full_name, :username, :email, :hashed_password, :cell_phone, :thumbnail)
    RETURNING id, tenant_id, full_name, username, email, hashed_password, email_verified, cell_phone, thumbnail, \
        is_active, created_at, updated_at;
"""


UPDATE_USER_PASSWORD_QUERY = """
    UPDATE users
    SET
        hashed_password = :hashed_password
    WHERE
        tenant_id = :tenant_id
        AND id = :id
    RETURNING id, tenant_id, full_name, username, email, hashed_password, email_verified, cell_phone, thumbnail, \
        is_active, created_at, updated_at;
"""


UPDATE_USER_THUMBNAIL_QUERY = """
    UPDATE users
    SET
        thumbnail = :thumbnail
    WHERE
        tenant_id = :tenant_id
        AND id = :id
    RETURNING id, tenant_id, full_name, username, email, hashed_password, email_verified, cell_phone, thumbnail, \
        is_active, created_at, updated_at;
"""


UPDATE_USER_BY_ID_QUERY = """
    UPDATE users
    SET
        full_name = :full_name,
        username = :username,
        email = :email,
        cell_phone = :cell_phone,
        thumbnail = :thumbnail,
        is_active = :is_active
    WHERE
        tenant_id = :tenant_id
        AND id = :id
    RETURNING id, tenant_id, full_name, username, email, hashed_password, email_verified, cell_phone, thumbnail, \
        is_active, created_at, updated_at;
"""


UPDATE_EMAIL_VERIFIED_BY_USER_ID_QUERY = """
    UPDATE users
    SET
        email_verified = TRUE
    WHERE
        tenant_id = :tenant_id
        AND id = :id
    RETURNING id, tenant_id, full_name, username, email, hashed_password, email_verified, cell_phone, thumbnail, \
        is_active, created_at, updated_at;
"""


DELETE_USERS_BY_ID_QUERY = """
    DELETE FROM users
    WHERE
        tenant_id = :tenant_id
        AND id = :id
    RETURNING id;
"""


REGISTER_ROLES_TO_USER_QUERY = """
    INSERT INTO roles_users(role_id, user_id)
    VALUES (:role_id, :user_id);
"""


REGISTER_PERMISSIONS_TO_USER_QUERY = """
    INSERT INTO permissions_users(permission_id, user_id)
    VALUES (:permission_id, :user_id);
"""


GET_ROLES_BY_USER_ID_QUERY = """
    SELECT
        r.id,
        r.slug,
        r.name
    FROM roles_users ru
    INNER JOIN roles r ON r.id = ru.role_id
    WHERE
        ru.user_id = :user_id;
"""


DELETE_ROLES_BY_USER_ID_QUERY = """
    DELETE
    FROM roles_users ru
    WHERE
        ru.user_id = :user_id
        AND ru.role_id IN (%s);
"""


GET_PERMISSIONS_BY_USER_ID_QUERY = """
    SELECT
        p.id, p.slug, p.name
    FROM
        permissions_users pu
        INNER JOIN permissions p ON pu.permission_id = p.id
    WHERE
        pu.user_id = :user_id;
"""


GET_PERMISSIONS_OF_ROLES_BY_USER_ID_QUERY = """
    SELECT DISTINCT
        p.id,
        p.slug,
        p.name
    FROM
        roles_users ru
        INNER JOIN permissions_roles pr ON pr.role_id = ru.role_id
        INNER JOIN permissions p ON pr.permission_id = p.id
    WHERE
        ru.user_id = :user_id;
"""


DELETE_PERMISSIONS_BY_USER_ID_QUERY = """
    DELETE
    FROM permissions_users pu
    WHERE
        pu.user_id = :user_id
        AND pu.permission_id IN (%s);
"""


HAS_ROLE_BY_USER_ID_QUERY = """
    SELECT
        true
    FROM
        users u
        INNER JOIN roles_users ru ON ru.user_id = u.id
        INNER JOIN roles r ON r.id = ru.role_id
    WHERE
        u.id = :user_id
        AND r.slug IN (%s)
    LIMIT 1;
"""


HAS_ROLES_PERMISSION_BY_USER_ID_QUERY = """
    SELECT
        true
    FROM
        permissions_roles pr
        INNER JOIN permissions p ON p.id = pr.permission_id
    WHERE
        pr.role_id IN(
            SELECT
                role_id FROM roles_users
            WHERE
                user_id = :user_id)
        AND p.slug IN (%s)
    LIMIT 1;
"""


HAS_PERMISSION_BY_USER_ID_QUERY = """
    SELECT
        true
    FROM
        permissions_users pu
        INNER JOIN permissions p ON pu.permission_id = p.id
    WHERE
        pu.user_id = :user_id
        AND p.slug = :slug;
"""


GET_USERS_BY_SLUG_ROLE_QUERY = """
    SELECT
        u.id,
        u.tenant_id,
        u.full_name,
        u.username,
        u.email,	u.cell_phone,
        u.thumbnail
        FROM
        users u
        INNER JOIN roles_users ru ON ru.user_id = u.id
        INNER JOIN roles r ON r.id = ru.role_id
    WHERE
        u.tenant_id= :tenant_id
        AND r.slug = :slug
        AND u.is_active
"""


class UsersRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.auth_service = auth_service

    async def get_user_by_email(self, *, email: EmailStr) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_EMAIL_QUERY, values={"email": email})
        if not user_record:
            return None
        return UserInDB(**user_record)

    async def get_user_by_tenant_id_and_email(self, *, tenant_id: UUID4, email: EmailStr) -> UserInDB:
        user_record = await self.db.fetch_one(
            query=GET_USER_BY_TENANT_ID_AND_EMAIL_QUERY, values={"tenant_id": tenant_id, "email": email}
        )
        if not user_record:
            return None
        return UserInDB(**user_record)

    async def get_user_by_username(self, *, username: str) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_USERNAME_QUERY, values={"username": username})
        if not user_record:
            return None
        return UserInDB(**user_record)

    async def get_user_by_tenant_and_username(self, *, tenant_id=UUID4, username: str) -> UserInDB:
        user_record = await self.db.fetch_one(
            query=GET_USER_BY_TENANT_ID_AND_USERNAME_QUERY, values={"tenant_id": tenant_id, "username": username}
        )
        if not user_record:
            return None
        return UserInDB(**user_record)

    async def get_user_by_id(self, *, tenant_id: UUID4, id: UUID4) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_ID_QUERY, values={"tenant_id": tenant_id, "id": id})
        if not user_record:
            return None
        return UserInDB(**user_record)

    async def get_user_full_by_id(self, *, id: UUID4) -> UserFull:
        user = await self.db.fetch_one(query=GET_USER_BY_ID_QUERY, values={"id": id})
        if not user:
            return None

        user = await self.get_full_user_by_user(user=user)

        return UserFull(**user)

    async def register_new_user(self, *, tenant_id: UUID4, new_user: UserCreate) -> UserInDB:
        # make sure email isn't already taken
        if await self.get_user_by_email(email=new_user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That email is already taken. Please try register with another one.",
            )
        # make sure username isn't already taken
        if await self.get_user_by_username(username=new_user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That username is already taken. Please try another one.",
            )

        hashed_password = self.auth_service.create_password(plaintext_password=new_user.password)
        create_user = UserWithTenantCreate(
            **new_user.dict(exclude={"password", "roles", "permissions"}),
            tenant_id=tenant_id,
            hashed_password=hashed_password,
        )

        async with self.db.transaction():
            created_user = await self.db.fetch_one(query=REGISTER_NEW_USER_QUERY, values=create_user.dict())
            created_user = UserInDB(**created_user, roles=None, permissions=None)

            if new_user.roles and len(new_user.roles) > 0:
                await self.register_roles_user(user=created_user, roles=new_user.roles)

            if new_user.permissions and len(new_user.permissions) > 0:
                await self.register_permissions_user(user=created_user, permissions=new_user.permissions)

            user_roles = await self.get_roles_by_user_id(user_id=created_user.id)
            user_permissions = await self.get_permissions_roles_by_user_id(user_id=created_user.id)
            user_extra_permissions = await self.get_permissions_by_user_id(user_id=created_user.id)

            user = created_user.dict()

            if user_roles:
                user["roles"] = [Role(**dict(r)) for r in user_roles]

            if user_permissions:
                user["permissions"] = [Permission(**dict(r)) for r in user_permissions]

            if user_extra_permissions:
                user["extra_permissions"] = [Permission(**dict(r)) for r in user_extra_permissions]

            return UserFull(**user)

    async def update_password(self, *, tenant_id: UUID4, id: UUID4, password: str) -> UserPublic:
        hashed_password = self.auth_service.create_password(plaintext_password=password)
        user = await self.db.fetch_one(
            query=UPDATE_USER_PASSWORD_QUERY,
            values={"tenant_id": tenant_id, "id": id, "hashed_password": hashed_password},
        )

        return UserPublic(**user)

    async def get_all_users(
        self,
        *,
        tenant_id: UUID4,
        current_page: int = 1,
        per_page: int = 10,
        filters: List[str],
        sorts: Optional[str],
    ) -> PageModel:
        users = Table("users")
        select_query = (
            Query.from_(users)
            .select(
                users.id,
                users.tenant_id,
                users.full_name,
                users.username,
                users.email,
                users.hashed_password,
                users.email_verified,
                users.cell_phone,
                users.thumbnail,
                users.is_active,
                users.created_at,
                users.updated_at,
            )
            .where(users.tenant_id == Parameter(":tenant_id"))
        )

        count_query = Query.from_(users).where(users.tenant_id == Parameter(":tenant_id"))

        return await self.get_page_by_params(
            table=users,
            select_query=select_query,
            count_query=count_query,
            tenant_id=tenant_id,
            filters=filters,
            sorts=sorts,
            current_page=current_page,
            per_page=per_page,
            type_schema=UserSummary,
        )

    async def update_user(self, *, user: UserInDB, user_update: UserUpdate) -> UserInDB:
        if user_update.email and user_update.email != user.email:
            # make sure email isn't already taken
            if await self.get_user_by_email(email=user_update.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="That email is already taken. Please try register with another one.",
                )

        if user_update.username and user_update.username != user.username:
            # make sure username isn't already taken
            if await self.get_user_by_username(username=user_update.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="That username is already taken. Please try another one.",
                )

        user_update_params = user.copy(update=user_update.dict(exclude_unset=True))
        updated_user = await self.db.fetch_one(
            query=UPDATE_USER_BY_ID_QUERY,
            values=user_update_params.dict(exclude={"email_verified", "hashed_password", "created_at", "updated_at"}),
        )

        user_in_db = UserInDB(**updated_user)
        return await self.get_full_user_by_user(user=user_in_db)

    async def delete_user(self, *, tenant_id: UUID4, user: UserInDB) -> UUID4:
        return await self.db.execute(query=DELETE_USERS_BY_ID_QUERY, values={"tenant_id": tenant_id, "id": user.id})

    async def get_roles_by_user_id(self, *, user_id: UUID4) -> List[RoleUser]:
        user_roles = await self.db.fetch_all(query=GET_ROLES_BY_USER_ID_QUERY, values={"user_id": user_id})
        if not user_roles:
            return None
        return user_roles

    async def get_users_by_slug_role(self, *, tenant_id: UUID4, slug: str) -> Optional[List[UserSummary]]:
        users_in_db = await self.db.fetch_all(
            query=GET_USERS_BY_SLUG_ROLE_QUERY, values={"tenant_id": tenant_id, "slug": slug}
        )
        if not users_in_db:
            return None
        return users_in_db

    async def get_permissions_by_user_id(self, *, user_id: UUID4) -> List[PermissionUserInDB]:
        user_permissions = await self.db.fetch_all(query=GET_PERMISSIONS_BY_USER_ID_QUERY, values={"user_id": user_id})
        if not user_permissions:
            return None
        return user_permissions

    async def get_permissions_roles_by_user_id(self, *, user_id: UUID4) -> List[PermissionUserInDB]:
        user_permissions = await self.db.fetch_all(
            query=GET_PERMISSIONS_OF_ROLES_BY_USER_ID_QUERY, values={"user_id": user_id}
        )
        if not user_permissions:
            return None
        return user_permissions

    async def has_roles_by_user_id(self, *, user_id: UUID4, slugs: List[str]) -> bool:
        return await self.db.fetch_val(
            query=HAS_ROLE_BY_USER_ID_QUERY % ",".join(map("'{}'".format, slugs)), values={"user_id": user_id}
        )

    async def has_roles_permission_by_user_id(self, *, user_id: UUID4, slugs: List[str]) -> Optional[bool]:
        return await self.db.fetch_val(
            query=HAS_ROLES_PERMISSION_BY_USER_ID_QUERY % ",".join(map("'{}'".format, slugs)),
            values={"user_id": user_id},
        )

    async def has_permission_by_user_id(self, *, user_id: UUID4, slug: str) -> Optional[bool]:
        return await self.db.fetch_val(query=HAS_PERMISSION_BY_USER_ID_QUERY, values={"user_id": user_id, "slug": slug})

    async def authenticate_user(self, *, email: EmailStr, password: str) -> Optional[UserInDB]:
        # make user user exists in db
        user = await self.get_user_by_email(email=email)
        if not user:
            return None
        # if submitted password doesn't match
        if not self.auth_service.verify_password(plain_password=password, hashed_password=user.hashed_password):
            return None
        return user

    async def register_roles_user(self, *, user: UserInDB, roles: List[UUID4]) -> None:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user is necessary to add role.",
            )

        if not roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one role is required to add the user.",
            )

        roles_for_user = [{"role_id": str(r), "user_id": str(user.id)} for r in roles]
        await self.db.execute_many(query=REGISTER_ROLES_TO_USER_QUERY, values=roles_for_user)

        return None

    async def register_permissions_user(self, *, user: UserInDB, permissions: List[UUID4]) -> None:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user is necessary to add role.",
            )

        if not permissions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one role is required to add the user.",
            )

        permissions_for_user = [{"permission_id": str(r), "user_id": str(user.id)} for r in permissions]
        await self.db.execute_many(query=REGISTER_PERMISSIONS_TO_USER_QUERY, values=permissions_for_user)

        return None

    async def delete_roles_user(self, *, user: UserInDB, roles: List[UUID4]) -> UserFull:
        roles = [str(r) for r in roles]
        self.logger.warn(roles)
        await self.db.execute(
            query=DELETE_ROLES_BY_USER_ID_QUERY % ",".join(map("'{}'".format, roles)), values={"user_id": user.id}
        )

        return await self.get_full_user_by_user(user=user)

    async def delete_permissions_user(self, *, user: UserInDB, permissions: List[UUID4]) -> UserFull:
        await self.db.execute(
            query=DELETE_PERMISSIONS_BY_USER_ID_QUERY % ",".join(map("'{}'".format, permissions)),
            values={"user_id": user.id},
        )

        return await self.get_full_user_by_user(user=user)

    async def get_full_user_by_user(self, *, user: UserInDB) -> UserFull:
        user_roles = await self.get_roles_by_user_id(user_id=user.id)
        user_permissions = await self.get_permissions_roles_by_user_id(user_id=user.id)
        user_extra_permissions = await self.get_permissions_by_user_id(user_id=user.id)

        user = user.dict()

        if user_roles:
            user["roles"] = [Role(**dict(r)) for r in user_roles]

        if user_permissions:
            user["permissions"] = [Permission(**dict(r)) for r in user_permissions]

        if user_extra_permissions:
            user["extra_permissions"] = [Permission(**dict(r)) for r in user_extra_permissions]

        return UserFull(**user)

    async def update_thumbnail(self, *, user: UserInDB, file: UploadFile) -> UserPublic:
        async with self.db.transaction():
            file_ext = "png" if "png" in file.content_type else "jpg"
            file_name = f"{user.full_name.lstrip().replace(' ', '_').strip().lower()}_{user.id}.{file_ext}"

            user = await self.db.fetch_one(
                query=UPDATE_USER_THUMBNAIL_QUERY,
                values={"tenant_id": user.tenant_id, "id": user.id, "thumbnail": file_name},
            )

            async with aiofiles.open(f"uploads/profiles/{file_name}", "wb") as out_file:
                content = await file.read()  # async read
                await out_file.write(content)  # async write

            s3 = boto3.client("s3")
            with open(f"uploads/profiles/{file_name}", "rb") as s3_file:
                s3.upload_fileobj(s3_file, S3_BUCKET, f"profiles/{file_name}")

            return UserPublic(**user)

    async def get_s3_url_thumbnail_s3(self, *, filename: str) -> str:
        return s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": f"profiles/{filename}",
            },
            ExpiresIn=S3_EXPIRES_IN,
        )

    async def get_redis_token_by_user(self, *, user: UserInDB, user_agent: str) -> Token:
        user_roles = await self.get_roles_by_user_id(user_id=user.id)
        user_permissions = await self.get_permissions_roles_by_user_id(user_id=user.id)
        user_extra_permissions = await self.get_permissions_by_user_id(user_id=user.id)

        token = Token(
            id=f"{str(user.id)}-{secrets.token_hex(6)}",
            tenant_id=str(user.tenant_id),
            user_id=str(user.id),
            name=user.full_name,
            username=user.username,
            email=user.email,
            device=user_agent,
        )

        if user_roles:
            roles = [Role(**dict(r)).slug for r in user_roles]
            token.roles = ",".join(roles)

        if user_permissions:
            permissions = [Permission(**dict(r)).slug for r in user_permissions]
            token.permissions = ",".join(permissions)

        if user_extra_permissions:
            extra_permissions = [Permission(**dict(r)).slug for r in user_extra_permissions]
            token.extra_permissions = ",".join(extra_permissions)

        return token

    async def confirm_email(self, *, tenant_id: UUID4, user_id: UUID4) -> Optional[UserPublic]:
        user = await self.get_user_by_id(tenant_id=tenant_id, id=user_id)

        if user:
            updated_user = await self.db.fetch_one(
                query=UPDATE_EMAIL_VERIFIED_BY_USER_ID_QUERY,
                values={"tenant_id": user.tenant_id, "id": user.id},
            )

            user_in_db = UserPublic(**updated_user)
            return user_in_db

        return None
