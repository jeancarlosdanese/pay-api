from typing import List
from uuid import uuid4
from pydantic.types import UUID4
import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.schemas.tenant import TenantWithUserCreate, TenantInDB

# decorate all tests with @pytest.mark.asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
def new_tenant(get_cnpj: str):
    return TenantWithUserCreate(
        **{
            "name": "Name test",
            "brand": "Brand test",
            "type": "Jurídica",
            "cpf_cnpj": get_cnpj,
            "email": "test@test.com",
            "subdomain": "test",
            "domain": "test.com",
            "admin_user": {
                "full_name": "Jean Carlos Danese",
                "email": "jean@danese.com.br",
                "username": "jeandanese",
                "cell_phone": "(49) 99966-9869",
                "password": "jean1234",
                "password_confirmation": "jean1234",
            },
        },
    )


class TestTenantsRoutes:
    @pytest.mark.asyncio
    async def test_routes_exist(self, app: FastAPI, client_authorized: AsyncClient) -> None:
        res = await client_authorized.post(app.url_path_for("tenants:create-tenant"), json={})
        assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        res = await client_authorized.get(app.url_path_for("tenants:get-tenant-by-id", id=str(uuid4())))
        assert res.status_code == HTTP_404_NOT_FOUND
        res = await client_authorized.get(app.url_path_for("tenants:get-all-tenants"))
        assert res.status_code == HTTP_200_OK
        res = await client_authorized.put(app.url_path_for("tenants:update-tenant-by-id", id=str(uuid4())))
        assert res.status_code != HTTP_404_NOT_FOUND
        res = await client_authorized.delete(app.url_path_for("tenants:delete-tenant-by-id", id=str(uuid4())))
        assert res.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_invalid_input_raises_error(self, app: FastAPI, client_authorized: AsyncClient) -> None:
        res = await client_authorized.post(app.url_path_for("tenants:create-tenant"), json={})
        print(res.json())
        assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


class TestCreateTenant:
    async def test_valid_input_creates_tenant(
        self, app: FastAPI, client_authorized: AsyncClient, new_tenant: TenantWithUserCreate
    ) -> None:
        res = await client_authorized.post(app.url_path_for("tenants:create-tenant"), json=new_tenant.dict())
        assert res.status_code == HTTP_201_CREATED
        # created_tenant = TenantCreate(**res.json())
        # assert created_tenant == new_tenant


#     @pytest.mark.parametrize(
#         "invalid_payload, status_code",
#         (
#             (None, HTTP_422_UNPROCESSABLE_ENTITY),
#             ({}, HTTP_422_UNPROCESSABLE_ENTITY),
#             ({"name": "test_name"}, HTTP_422_UNPROCESSABLE_ENTITY),
#             (
#                 {
#                     "name": "test_name",
#                     "type": "Física",
#                     "email": "test@test.com",
#                     "subdomain": "test",
#                     "domain": "test.com",
#                 },
#                 HTTP_400_BAD_REQUEST,
#             ),
#             (
#                 {
#                     "name": "test_name 2",
#                     "type": "Jurídica",
#                     "email": "test@test.com",
#                     "subdomain": "test",
#                     "domain": "test.com",
#                 },
#                 HTTP_400_BAD_REQUEST,
#             ),
#             (
#                 {
#                     "name": "test_name 2",
#                     "type": "Física",
#                     "email": "test2@test.com",
#                     "subdomain": "test",
#                     "domain": "test.com",
#                 },
#                 HTTP_400_BAD_REQUEST,
#             ),
#             (
#                 {
#                     "name": "test_name 2",
#                     "type": "Jurídica",
#                     "email": "test2@test.com",
#                     "subdomain": "test2",
#                     "domain": "test.com",
#                 },
#                 HTTP_201_CREATED,
#             ),
#             (
#                 {
#                     "name": "test_name 2",
#                     "type": "Física",
#                     "email": "test2@test.com",
#                     "subdomain": "test2",
#                     "domain": "test2.com",
#                 },
#                 HTTP_400_BAD_REQUEST,
#             ),
#         ),
#     )
#     async def test_invalid_input_raises_error(
#         self,
#         app: FastAPI,
#         client_authorized: AsyncClient,
#         invalid_payload: dict,
#         status_code: int,
#         get_cpf: str,
#         get_cnpj: str,
#     ) -> None:
#         if invalid_payload and ("type" in invalid_payload):
#             invalid_payload["cpf_cnpj"] = get_cpf if invalid_payload["type"] == "Física" else get_cnpj
#         res = await client_authorized.post(app.url_path_for("tenants:create-tenant"), json=invalid_payload)
#         assert res.status_code == status_code


# class TestGetTenant:
#     async def test_get_tenant_by_id(
#         self, app: FastAPI, client_authorized: AsyncClient, test_tenant_fixed: TenantInDB
#     ) -> None:
#         res = await client_authorized.get(app.url_path_for("tenants:get-tenant-by-id", id=test_tenant_fixed.id))
#         assert res.status_code == HTTP_200_OK
#         tenant = TenantInDB(**res.json())
#         assert tenant.id == test_tenant_fixed.id

#     @pytest.mark.parametrize(
#         "id, status_code",
#         (
#             (str(uuid4()), HTTP_404_NOT_FOUND),
#             (-1, HTTP_422_UNPROCESSABLE_ENTITY),
#             (None, HTTP_422_UNPROCESSABLE_ENTITY),
#         ),
#     )
#     async def test_wrong_id_returns_error(
#         self, app: FastAPI, client_authorized: AsyncClient, id: UUID4, status_code: int
#     ) -> None:
#         res = await client_authorized.get(app.url_path_for("tenants:get-tenant-by-id", id=id))
#         assert res.status_code == status_code

#     async def test_get_all_tenants_returns_valid_response(
#         self, app: FastAPI, client_authorized: AsyncClient, test_tenant: TenantInDB
#     ) -> None:
#         res = await client_authorized.get(app.url_path_for("tenants:get-all-tenants"))
#         assert res.status_code == HTTP_200_OK
#         assert isinstance(res.json(), list)
#         assert len(res.json()) > 0
#         tenants = [TenantInDB(**r) for r in res.json()]

#         assert test_tenant in tenants


# class TestUpdateTenant:
#     @pytest.mark.parametrize(
#         "tenant_name, attrs_to_change, values",
#         (
#             ("to_tenant_1", ["cep"], ["89999-999"]),
#             ("to_tenant_2", ["name"], ["new fake tenant name"]),
#             ("to_tenant_3", ["email"], ["newfake@tenant.com"]),
#             ("to_tenant_4", ["cpf_cnpj"], ["18.999.870/0222-31"]),
#             ("to_tenant_5", ["domain"], ["newtenant.com"]),
#             ("to_tenant_6", ["subdomain", "domain"], ["newfake", "newtenant.com"]),
#         ),
#     )
#     async def test_update_tenant_with_valid_input(
#         self,
#         app: FastAPI,
#         client_authorized: AsyncClient,
#         test_tenant_param: TenantInDB,
#         attrs_to_change: List[str],
#         values: List[str],
#     ) -> None:
#         update_tenant = {attrs_to_change[i]: values[i] for i in range(len(attrs_to_change))}
#         res = await client_authorized.put(
#             app.url_path_for("tenants:update-tenant-by-id", id=test_tenant_param.id), json=update_tenant
#         )
#         assert res.status_code == HTTP_200_OK

#         updated_tenant = TenantInDB(**res.json())
#         assert updated_tenant.id == test_tenant_param.id  # make sure it's the same tenant
#         # make sure that any attribute we updated has changed to the correct value
#         for i in range(len(attrs_to_change)):
#             assert getattr(updated_tenant, attrs_to_change[i]) != getattr(test_tenant_param, attrs_to_change[i])
#             assert getattr(updated_tenant, attrs_to_change[i]) == values[i]
#         # make sure that no other attributes' values have changed
#         for attr, value in updated_tenant.dict().items():
#             if attr not in attrs_to_change and attr != "updated_at":
#                 assert getattr(test_tenant_param, attr) == value

#     @pytest.mark.parametrize(
#         "id, payload, status_code",
#         (
#             (-1, {"name": "test"}, HTTP_422_UNPROCESSABLE_ENTITY),
#             (0, {"name": "test2"}, HTTP_422_UNPROCESSABLE_ENTITY),
#             (str(uuid4()), {"name": "test3"}, HTTP_404_NOT_FOUND),
#         ),
#     )
#     async def test_update_tenant_with_invalid_input_throws_error(
#         self,
#         app: FastAPI,
#         client_authorized: AsyncClient,
#         id: int,
#         payload: dict,
#         status_code: int,
#     ) -> None:
#         update_tenant = {"update_tenant": payload}
#         res = await client_authorized.put(app.url_path_for("tenants:update-tenant-by-id", id=id), json=update_tenant)
#         assert res.status_code == status_code


# class TestDeleteTenant:
#     async def test_cant_delete_tenant_users_tenant_id_fkey(
#         self, app: FastAPI, client_authorized: AsyncClient, test_tenant_fixed: TenantInDB
#     ) -> None:
#         # ensure that the tenant no longer exists
#         res = await client_authorized.get(app.url_path_for("tenants:get-tenant-by-id", id=test_tenant_fixed.id))
#         assert res.status_code == HTTP_200_OK
#         # delete the tenant
#         res = await client_authorized.delete(
#             app.url_path_for("tenants:delete-tenant-by-id", id=str(test_tenant_fixed.id))
#         )
#         assert res.status_code == HTTP_400_BAD_REQUEST
#         error_body: dict = res.json()
#         assert 'foreign key constraint "users_tenant_id_fkey"' in error_body["message"]

#     @pytest.mark.parametrize(
#         "id, status_code",
#         (
#             (str(uuid4()), 404),
#             (0, 422),
#             (-1, 422),
#             (None, 422),
#         ),
#     )
#     async def test_delete_tenant_with_invalid_input(
#         self, app: FastAPI, client_authorized: AsyncClient, id: UUID4, status_code: int
#     ) -> None:
#         res = await client_authorized.delete(app.url_path_for("tenants:delete-tenant-by-id", id=id))
#         assert res.status_code == status_code
