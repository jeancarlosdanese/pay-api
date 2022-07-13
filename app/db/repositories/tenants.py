import aiofiles
from typing import List
from fastapi import HTTPException, UploadFile, status
from pydantic.types import UUID4

from app.schemas.tenant import TenantCreate, TenantInDB, TenantUpdate
from .base import BaseRepository


GET_TENANT_BY_API_KEY_QUERY = """
    SELECT id, name, brand, type, cpf_cnpj, ie, cep, street, number, complement, neighborhood, city, state, \
        email, email_verified, phone, cell_phone, api_key, subdomain, domain, is_active, \
            is_master, created_at, updated_at
    FROM tenants
    WHERE api_key = :api_key
    LIMIT 1;
"""


GET_TENANT_BY_SUBDOMAIN_AND_DOMAIN_QUERY = """
    SELECT id, name, brand, type, cpf_cnpj, ie, cep, street, number, complement, neighborhood, city, state, \
        email, email_verified, phone, cell_phone, api_key, subdomain, domain, is_active, \
            is_master, created_at, updated_at
    FROM tenants
    WHERE subdomain = :subdomain
        AND domain = :domain
    LIMIT 1;
"""


GET_TENANT_BY_ID_QUERY = """
    SELECT id, name, brand, type, cpf_cnpj, ie, cep, street, number, complement, neighborhood, city, state, \
        email, email_verified, phone, cell_phone, api_key, subdomain, domain, is_active, \
            is_master, created_at, updated_at
    FROM tenants
    WHERE id = :id;
"""


CREATE_TENANT_QUERY = """
    INSERT INTO tenants (name, brand, type, cpf_cnpj, ie, cep, street, number, complement, neighborhood, city, \
        state, email, phone, cell_phone, api_key, subdomain, domain)
    VALUES (:name, :brand, :type, :cpf_cnpj, :ie, :cep, :street, :number, :complement, :neighborhood, :city, \
        :state, :email, :phone, :cell_phone, :api_key, :subdomain, :domain)
    RETURNING id, name, brand, type, cpf_cnpj, ie, cep, street, number, complement, neighborhood, city, \
        state, email, email_verified, phone, cell_phone, api_key, subdomain, domain, is_active, is_master, \
            created_at, updated_at;
"""


GET_ALL_TENANTS_QUERY = """
    SELECT id, name, brand, type, cpf_cnpj, ie, cep, street, number, complement, neighborhood, city, state, \
        email, email_verified, phone, cell_phone, api_key, subdomain, domain, is_active, is_master, \
            created_at, updated_at
    FROM tenants;
"""


UPDATE_TENANT_BY_ID_QUERY = """
    UPDATE
        tenants
    SET
        name = :name,
        brand = :brand,
        type = :type,
        cpf_cnpj = :cpf_cnpj,
        ie = :ie,
        cep = :cep,
        street = :street,
        number = :number,
        complement = :complement,
        neighborhood = :neighborhood,
        city = :city,
        state = :state,
        email = :email,
        phone = :phone,
        cell_phone = :cell_phone,
        subdomain = :subdomain,
        domain = :domain,
        is_active = :is_active
    WHERE
        id = :id
    RETURNING id, name, brand, type, cpf_cnpj, ie, cep, street, number, complement, neighborhood, city, state, \
        email, email_verified, phone, cell_phone, api_key, subdomain, domain, is_active, is_master, \
            created_at, updated_at;
"""


UPDATE_EMAIL_VERIFIED_BY_ID_QUERY = """
    UPDATE
        tenants
    SET
        email_verified = TRUE
    WHERE
        id = :id
    RETURNING id, name, brand, type, cpf_cnpj, ie, cep, street, number, complement, neighborhood, city, state, \
        email, email_verified, phone, cell_phone, api_key, subdomain, domain, is_active, is_master, \
            created_at, updated_at;
"""


DELETE_TENANT_BY_ID_QUERY = """
    DELETE FROM tenants
    WHERE id = :id
    RETURNING id;
"""


GET_UNIQUE_TENANT_BY_FIELD_QUERY = """
    SELECT 1
    FROM tenants
    -- WHERE :field = :value
    -- LIMIT 1;
"""


class TenantsRepository(BaseRepository):
    """
    All database actions associated with the Tenant resource
    """

    async def get_tenant_by_subdomain_and_domain(self, *, subdomain: str, domain: str) -> TenantInDB:
        tenant = await self.db.fetch_one(
            query=GET_TENANT_BY_SUBDOMAIN_AND_DOMAIN_QUERY, values={"subdomain": subdomain, "domain": domain}
        )
        if not tenant:
            return None
        return TenantInDB(**tenant)

    async def get_tenant_by_api_key(self, *, api_key: str) -> TenantInDB:
        tenant = await self.db.fetch_one(query=GET_TENANT_BY_API_KEY_QUERY, values={"api_key": api_key})
        if not tenant:
            return None
        return TenantInDB(**tenant)

    async def get_all_tenants(self) -> List[TenantInDB]:
        tenants = await self.db.fetch_all(query=GET_ALL_TENANTS_QUERY)
        return tenants

    async def create_new_tenant(self, *, new_tenant: TenantCreate) -> TenantInDB:
        query_values = new_tenant.dict()
        tenant = await self.db.fetch_one(query=CREATE_TENANT_QUERY, values=query_values)

        return TenantInDB(**tenant)

    async def get_tenant_by_id(self, *, id: UUID4) -> TenantInDB:
        tenant = await self.db.fetch_one(query=GET_TENANT_BY_ID_QUERY, values={"id": id})
        if not tenant:
            return None

        return TenantInDB(**tenant)

    async def update_tenant(self, *, id: UUID4, tenant_update: TenantUpdate) -> TenantInDB:
        tenant = await self.get_tenant_by_id(id=id)

        if not tenant:
            return None

        tenant_update_params = tenant.copy(update=tenant_update.dict(exclude_unset=True))
        if tenant_update_params.name is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant name. Cannot be None.")

        updated_tenant = await self.db.fetch_one(
            query=UPDATE_TENANT_BY_ID_QUERY,
            values=tenant_update_params.dict(
                exclude={"email_verified", "api_key", "is_master", "created_at", "updated_at"}
            ),
        )
        return TenantInDB(**updated_tenant)

    async def delete_tenant_by_id(self, *, id: UUID4) -> UUID4:
        tenant = await self.get_tenant_by_id(id=id)
        if not tenant:
            return None
        deleted_id = await self.db.execute(query=DELETE_TENANT_BY_ID_QUERY, values={"id": id})
        return deleted_id

    async def update_logo(self, *, tenant_id: UUID4, file: UploadFile):
        file_ext = "png" if "png" in file.content_type else "jpg"
        file_name = f"logo_{tenant_id}.{file_ext}"

        async with aiofiles.open(f"static/{file_name}", "wb") as out_file:
            content = await file.read()  # async read
            await out_file.write(content)  # async write

    async def update_email_verified_by_id(self, *, id: UUID4) -> TenantInDB:
        tenant = await self.db.fetch_one(query=UPDATE_EMAIL_VERIFIED_BY_ID_QUERY, values={"id": id})
        if not tenant:
            return None

        return TenantInDB(**tenant)
