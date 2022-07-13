import asyncio
import random
import string
import warnings
import os
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from databases import Database
import alembic
from alembic.config import Config
import pytest_asyncio

from app.core.config import DOMAIN_MAIN, EMAIL_MAIN, HOST_MAIN, JWT_TOKEN_PREFIX_AUTH, SECRET_KEY

from validate_docbr import CPF, CNPJ
from app.schemas.role import RoleInDB

from app.schemas.tenant import TenantCreate, TenantInDB
from app.schemas.token import AccessToken
from app.schemas.user import UserCreate, UserFull, UserInDB
from app.db.repositories.tenants import TenantsRepository
from app.db.repositories.users import UsersRepository
from app.db.repositories.roles import RolesRepository
from app.services import auth_service

from starlette.status import (
    HTTP_200_OK,
)


class Domain:
    def __init__(self, subdomain: str, domain: str):
        self.subdomain = subdomain
        self.domain = f"{domain}.com.br"


# ERROR: python3.9/site-packages/aioredis/connection.py:794> exception=RuntimeError('Event loop is closed')>
# to fix this: https://stackoverflow.com/questions/56236637/using-pytest-fixturescope-module-with-pytest-mark-asyncio
@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop
    loop.close()


# Apply migrations at beginning and end of testing session
@pytest_asyncio.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")
    alembic.command.upgrade(config, "head")
    yield
    alembic.command.downgrade(config, "base")


# Create a new application for testing
@pytest_asyncio.fixture(scope="session")
def app(apply_migrations: None) -> FastAPI:
    from app.main import get_application

    return get_application()


# Grab a reference to our database when needed
@pytest_asyncio.fixture
def db(app: FastAPI) -> Database:
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    return app.state._db


# Create cnpj instance
@pytest_asyncio.fixture
def get_cnpj() -> str:
    cnpj = CNPJ()
    return cnpj.generate(True)


# Create cpf instance
@pytest_asyncio.fixture
def get_cpf() -> str:
    cpf = CPF()
    return cpf.generate(True)


# Create random subdomain and domain
@pytest_asyncio.fixture
def domain() -> Domain:
    subdomain = "".join(random.choice(string.ascii_lowercase) for _ in range(3))
    domain = "".join(random.choice(string.ascii_lowercase) for _ in range(random.randint(3, 15)))
    return Domain(subdomain=subdomain, domain=domain)


# Make requests in our tests
@pytest_asyncio.fixture
async def client(app: FastAPI, domain: Domain) -> AsyncClient:
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    async with LifespanManager(app):
        base_url = f"http://{domain.subdomain}.{domain.domain}:8000"

        async with AsyncClient(
            app=app,
            base_url=base_url,
            headers={
                "Content-Type": "application/json",
            },
        ) as client:
            yield client


@pytest_asyncio.fixture
async def client_host_authorized(app: FastAPI, domain: Domain) -> AsyncClient:
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    async with LifespanManager(app):
        base_url = f"http://{HOST_MAIN}.{DOMAIN_MAIN}:8000"

        async with AsyncClient(
            app=app,
            base_url=base_url,
            headers={
                "Content-Type": "application/json",
                "Origin": base_url,
            },
        ) as client:
            yield client


# Make requests in our tests
@pytest_asyncio.fixture
async def client_for_tenant(app: FastAPI) -> AsyncClient:
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    async with LifespanManager(app):
        base_url = "http://localhost"

        async with AsyncClient(
            app=app, base_url=base_url, headers={"Content-Type": "application/json", "X-API-Key": "1234567890"}
        ) as client:
            yield client


@pytest_asyncio.fixture
async def access_token(app: FastAPI, client: AsyncClient, test_master_user: UserInDB) -> AccessToken:
    client.headers["Content-Type"] = "application/x-www-form-urlencoded"
    login_data = {
        "username": f"{EMAIL_MAIN}",
        "password": "master123",
    }
    res = await client.post(
        app.url_path_for("auth:user-login"),
        data=login_data,
    )
    assert res.status_code == HTTP_200_OK

    return AccessToken(**res.json())


@pytest_asyncio.fixture
async def client_authorized(app: FastAPI, client: AsyncClient, access_token: AccessToken) -> AsyncClient:
    base_url = f"http://{HOST_MAIN}.{DOMAIN_MAIN}"

    client.headers = {
        "Authorization": f"{access_token.token_type} {access_token.access_token}",
        "Origin": base_url,
    }

    return client


@pytest_asyncio.fixture
def client_authorized_2(client: AsyncClient, test_user_6: UserInDB) -> AsyncClient:
    access_token = auth_service.create_access_token_for_user(user=test_user_6, secret_key=str(SECRET_KEY))
    client.headers = {
        **client.headers,
        "Authorization": f"{JWT_TOKEN_PREFIX_AUTH} {access_token}",
    }
    return client


@pytest_asyncio.fixture
async def test_tenant_fixed(db: Database) -> TenantInDB:
    tenants_repo = TenantsRepository(db)
    tenant = await tenants_repo.get_tenant_by_subdomain_and_domain(subdomain=HOST_MAIN, domain=DOMAIN_MAIN)

    if tenant:
        return tenant

    cnpj = CNPJ()
    new_tenant = TenantCreate(
        name="Tenant Test Fix",
        type="Jurídica",
        cpf_cnpj=cnpj.generate(True),
        email=f"{EMAIL_MAIN}",
        subdomain="vicos",
        domain=f"{DOMAIN_MAIN}",
    )

    return await tenants_repo.create_new_tenant(new_tenant=new_tenant)


@pytest_asyncio.fixture
async def test_tenant(db: Database) -> TenantInDB:
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    tenants_repo = TenantsRepository(db)
    cnpj = CNPJ()
    new_tenant = TenantCreate(
        name="Tenant Test",
        type="Jurídica",
        cpf_cnpj=cnpj.generate(True),
        email="tenant@tenant.com",
        subdomain="tenant",
        domain="tenant.com",
    )

    return await tenants_repo.create_new_tenant(new_tenant=new_tenant)


@pytest_asyncio.fixture(params=["tenant_name"])
async def test_tenant_param(
    db: Database,
    domain: Domain,
    tenant_name,
) -> TenantInDB:
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    return await create_tenant(db=db, domain=domain, param=tenant_name)


async def create_tenant(db: Database, domain: Domain, param: str) -> TenantInDB:
    tenants_repo = TenantsRepository(db)
    cnpj = CNPJ()
    new_tenant = TenantCreate(
        name="Tenant " + param,
        type="Jurídica",
        cpf_cnpj=cnpj.generate(True),
        email=param + f"@{domain.domain}",
        subdomain=domain.subdomain,
        domain=domain.domain,
    )

    return await tenants_repo.create_new_tenant(new_tenant=new_tenant)


@pytest_asyncio.fixture
async def test_role_master(db: Database) -> RoleInDB:
    roles_repo = RolesRepository(db)
    existing_role = await roles_repo.get_user_by_slug(slug="master")
    if not existing_role:
        return None
    return existing_role


@pytest_asyncio.fixture
async def test_role_administrator(db: Database) -> RoleInDB:
    roles_repo = RolesRepository(db)
    existing_role = await roles_repo.get_user_by_slug(slug="administrator")
    if not existing_role:
        return None
    return existing_role


@pytest_asyncio.fixture
async def test_master_user(db: Database, test_tenant_fixed: TenantInDB, test_role_master: RoleInDB) -> UserInDB:
    users_repo = UsersRepository(db)
    existing_user = await users_repo.get_user_by_email(email=f"{EMAIL_MAIN}")
    if existing_user:
        return existing_user

    new_user = UserCreate(
        tenant_id=str(test_tenant_fixed.id),
        email=f"{EMAIL_MAIN}",
        username="master",
        password="master123",
        roles=[str(test_role_master.id)],
    )
    return await users_repo.register_new_user(new_user=new_user)


@pytest_asyncio.fixture
async def test_admin_user(db: Database, test_tenant_fixed: TenantInDB, test_role_administrator: RoleInDB) -> UserInDB:
    new_user = UserCreate(
        tenant_id=str(test_tenant_fixed.id),
        email="admin@hyberica.io",
        username="admin",
        password="admin123",
        roles=[str(test_role_administrator.id)],
    )
    users_repo = UsersRepository(db)
    existing_user = await users_repo.get_user_by_email(email=new_user.email)
    if existing_user:
        return existing_user

    return await users_repo.register_new_user(new_user=new_user)


@pytest_asyncio.fixture(params=["tenant_name"])
async def test_user_param(
    db: Database,
    test_tenant_fixed: TenantInDB,
    test_master_user: UserInDB,
    test_role_administrator: UserFull,
    tenant_name,
) -> UserInDB:
    new_user = UserCreate(
        email=f"{tenant_name}@mariabonita.com",
        full_name=f"full name {tenant_name}",
        username=f"{tenant_name}",
        password="maria123",
        password_confirmation="maria123",
        roles=[str(test_role_administrator.id)],
    )
    users_repo = UsersRepository(db)
    existing_user = await users_repo.get_user_by_email(email=new_user.email)
    if existing_user:
        return existing_user
    return await users_repo.register_new_user(tenant_id=test_tenant_fixed.id, new_user=new_user)
