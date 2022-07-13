import jwt
import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)
from app.db.repositories.users import UsersRepository
from app.schemas.role import RoleInDB

from app.schemas.tenant import TenantInDB
from databases import Database
from app.schemas.token import AccessToken

from app.schemas.user import UserInDB, UserPublic
from app.services import auth_service


from app.core.config import SECRET_KEY, JWT_ALGORITHM, JWT_AUDIENCE_AUTH

pytestmark = pytest.mark.asyncio


class TestUserRoutes:
    async def test_routes_exist(
        self, app: FastAPI, client_authorized: AsyncClient, test_tenant_fixed: TenantInDB
    ) -> None:
        new_user = {
            "email": "test@email.io",
            "full_name": "test testing test",
            "username": "test_username",
            "password": "testpassword",
            "password_confirmation": "testpassword",
        }
        res = await client_authorized.post(app.url_path_for("users:register-new-user"), json=new_user)
        assert res.status_code != HTTP_404_NOT_FOUND


class TestUserRegistration:
    async def test_users_can_register_successfully(
        self,
        app: FastAPI,
        client_authorized: AsyncClient,
        db: Database,
        test_tenant_fixed: TenantInDB,
        test_role_administrator: RoleInDB,
    ) -> None:
        users_repo = UsersRepository(db)
        new_user = {
            "email": "liname@liname.io",
            "full_name": "liname sobrenome",
            "username": "linameliname",
            "password": "liname123",
            "password_confirmation": "liname123",
            "roles": [str(test_role_administrator.id)],
        }
        # make sure user doesn't exist yet
        user_in_db = await users_repo.get_user_by_email(email=new_user["email"])
        # res = await client_authorized.get(app.url_path_for("users:get-user-by-email"), id=test_tenant_fixed.id)
        assert user_in_db is None
        # send post request to create user and ensure it is successful
        res = await client_authorized.post(app.url_path_for("users:register-new-user"), json=new_user)
        created_user = UserInDB(**res.json())
        assert res.status_code == HTTP_201_CREATED
        # ensure that the user now exists in the db
        user_in_db = await users_repo.get_user_by_email(email=new_user["email"])
        assert user_in_db is not None
        assert user_in_db.email == new_user["email"]
        assert user_in_db.username == new_user["username"]
        # check that the user returned in the response is equal to the user in the database
        assert created_user.dict(
            exclude={"tenant_id", "hashed_password", "roles", "permissions", "extra_permissions"}
        ) == user_in_db.dict(exclude={"tenant_id", "hashed_password", "roles", "permissions", "extra_permissions"})

    @pytest.mark.parametrize(
        "tenant_name, attr, value, status_code",
        (
            ("to_users_3", "email", "invalid_email@one@two.io", 422),
            ("to_users_4", "password", "short", 422),
            ("to_users_5", "username", "liname@#$%^<>", 422),
            ("to_users_6", "username", "ab", 422),
        ),
    )
    async def test_user_registration_fails_with_invalid_fields(
        self,
        app: FastAPI,
        client_authorized: AsyncClient,
        attr: str,
        value: str,
        status_code: int,
        test_tenant_param: TenantInDB,
    ) -> None:
        new_user = {
            "email": "nottaken@email.io",
            "full_name": "nottaken not taken",
            "username": "not_taken_username",
            "password": "freepassword",
            "password_confirmation": "freepassword",
        }
        new_user[attr] = value
        res = await client_authorized.post(app.url_path_for("users:register-new-user"), json=new_user)
        assert res.status_code == status_code

    async def test_user_registration_fails_duplicated_email(
        self,
        app: FastAPI,
        client_authorized: AsyncClient,
        test_tenant_fixed: TenantInDB,
    ) -> None:
        new_user = {
            "tenant_id": str(test_tenant_fixed.id),
            "full_name": "nottaken not taken",
            "email": "nottaken@email.io",
            "username": "nottaken_username",
            "password": "freepassword",
            "password_confirmation": "freepassword",
        }
        res = await client_authorized.post(app.url_path_for("users:register-new-user"), json=new_user)
        assert res.status_code == 201

        new_user["username"] = "taken_username"
        res = await client_authorized.post(app.url_path_for("users:register-new-user"), json=new_user)
        assert res.status_code == 400

    async def test_users_saved_password_is_hashed(
        self,
        app: FastAPI,
        client_authorized: AsyncClient,
        db: Database,
        test_tenant_fixed: TenantInDB,
    ) -> None:
        users_repo = UsersRepository(db)
        new_user = {
            "full_name": "benedetto bleoo",
            "email": "benedetto@bleoo.io",
            "username": "benedetto",
            "password": "destinyschild",
            "password_confirmation": "destinyschild",
        }
        # send post request to create user and ensure it is successful
        res = await client_authorized.post(app.url_path_for("users:register-new-user"), json=new_user)
        assert res.status_code == HTTP_201_CREATED
        # ensure that the users password is hashed in the db
        # and that we can verify it using our auth service
        user_in_db = await users_repo.get_user_by_email(email=new_user["email"])
        assert user_in_db is not None
        assert user_in_db.hashed_password != new_user["password"]
        assert auth_service.verify_password(
            plain_password=new_user["password"],
            hashed_password=user_in_db.hashed_password,
        )


class TestAuthTokens:
    async def test_can_create_access_token_successfully(
        self,
        access_token: AccessToken,
        test_master_user: UserInDB,
    ) -> None:
        creds = jwt.decode(
            access_token.access_token, str(SECRET_KEY), audience=JWT_AUDIENCE_AUTH, algorithms=[JWT_ALGORITHM]
        )
        assert creds.get("sub") is not None
        assert creds["iss"] == str(test_master_user.tenant_id)
        assert creds["aud"] == JWT_AUDIENCE_AUTH


class TestUserLogin:
    async def test_user_can_login_successfully_and_receives_valid_token(
        self, app: FastAPI, client_host_authorized: AsyncClient, test_master_user: UserInDB
    ) -> None:
        client_host_authorized.headers["content-type"] = "application/x-www-form-urlencoded"
        login_data = {
            "username": test_master_user.email,
            "password": "master123",  # insert user's plaintext password
        }
        res = await client_host_authorized.post(app.url_path_for("auth:login-email-and-password"), data=login_data)
        assert res.status_code == HTTP_200_OK
        # check that token exists in response and has user encoded within it
        token = res.json().get("access_token")
        creds = jwt.decode(token, str(SECRET_KEY), audience=JWT_AUDIENCE_AUTH, algorithms=[JWT_ALGORITHM])
        assert "aud" in creds
        assert creds["aud"] == JWT_AUDIENCE_AUTH
        assert creds["iss"] == str(test_master_user.tenant_id)
        assert "sub" in creds
        assert creds["sub"] is not None
        # check that token is proper type
        assert "token_type" in res.json()
        assert res.json().get("token_type") == "bearer"

    @pytest.mark.parametrize(
        "tenant_name, credential, wrong_value, status_code",
        (
            ("to_login_0", "email", "wrong@email.com", 401),
            ("to_login_1", "email", None, 422),
            ("to_login_2", "email", "notemail", 401),
            ("to_login_3", "password", "wrongpassword", 401),
            ("to_login_4", "password", None, 422),
        ),
    )
    async def test_user_with_wrong_creds_doesnt_receive_token(
        self,
        app: FastAPI,
        client_host_authorized: AsyncClient,
        test_user_param: UserInDB,
        credential: str,
        wrong_value: str,
        status_code: int,
    ) -> None:
        client_host_authorized.headers["content-type"] = "application/x-www-form-urlencoded"
        user_data = test_user_param.dict()
        user_data["password"] = "maria123"  # insert user's plaintext password
        user_data[credential] = wrong_value
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"],  # insert password from parameters
        }
        res = await client_host_authorized.post(app.url_path_for("auth:login-email-and-password"), data=login_data)
        assert res.status_code == status_code
        assert "access_token" not in res.json()


class TestUserMe:
    async def test_authenticated_user_can_retrieve_own_data(
        self,
        app: FastAPI,
        client_authorized: AsyncClient,
        test_master_user: UserInDB,
    ) -> None:
        res = await client_authorized.get(app.url_path_for("profile:get-current-user"))
        assert res.status_code == HTTP_200_OK
        user = UserPublic(**res.json())
        assert user.email == test_master_user.email
        assert user.username == test_master_user.username
        assert user.id == test_master_user.id

    async def test_user_cannot_access_own_data_if_not_authenticated(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        res = await client.get(app.url_path_for("profile:get-current-user"))
        assert res.status_code == HTTP_401_UNAUTHORIZED


class TestGetAllUsers:
    async def test_get_all_users_with_right_role(
        self,
        app: FastAPI,
        client_authorized: AsyncClient,
        test_master_user: UserInDB,
    ) -> None:
        res = await client_authorized.get(
            app.url_path_for("users:get-all-users"), params={"username": test_master_user.username}
        )
        assert res.status_code == HTTP_200_OK
        result = res.json()
        first_row = result["rows"][0]
        user = UserPublic(**first_row)
        assert user.email == test_master_user.email
        assert user.username == test_master_user.username
        assert user.id == test_master_user.id
