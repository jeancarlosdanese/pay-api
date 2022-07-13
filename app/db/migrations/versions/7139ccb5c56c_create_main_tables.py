"""create_main_tables

Revision ID: 7139ccb5c56c
Revises:
Create Date: 2021-06-18 02:47:24.099147

"""
import secrets
from app.core.config import DOMAIN_MAIN, EMAIL_MAIN, HOST_MAIN
from app.schemas.enums import PersonType, StatesUF
from alembic import op
from passlib.context import CryptContext
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql.base import ENUM

from app.db.migrations.base import timestamps

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# revision identifiers, used by Alembic.
revision = "7139ccb5c56c"
down_revision = None
branch_labels = None
depends_on = None


def create_updated_at_trigger() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS
        $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )


def create_tenants_table() -> None:
    table = "tenants"
    state_ufs = tuple(StatesUF.values())
    person_types = tuple(PersonType.values())
    op.create_table(
        table,
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(140), nullable=False),
        sa.Column("brand", sa.String(140), nullable=True),
        sa.Column("type", ENUM(*person_types, name="person_types"), nullable=False),
        sa.Column("cpf_cnpj", sa.String(18), nullable=False),
        sa.Column("ie", sa.String(20), nullable=True),
        sa.Column("cep", sa.String(9), nullable=True),
        sa.Column("street", sa.String(140), nullable=True),
        sa.Column("number", sa.String(10), nullable=True),
        sa.Column("complement", sa.String(140), nullable=True),
        sa.Column("neighborhood", sa.String(140), nullable=True),
        sa.Column("city", sa.String(140), nullable=True),
        sa.Column(
            "state",
            ENUM(*state_ufs, name="state_ufs"),
            nullable=True,
        ),
        sa.Column("email", sa.String(140), nullable=False),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="False"),
        sa.Column("phone", sa.String(15), nullable=True),
        sa.Column("cell_phone", sa.String(15), nullable=True),
        sa.Column("subdomain", sa.String(10), nullable=False),
        sa.Column("domain", sa.String(140), nullable=False),
        sa.Column("api_key", sa.String(254), nullable=False),
        sa.Column("is_master", sa.Boolean, nullable=False, server_default="False"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="True"),
        *timestamps(),
    )
    op.create_index(op.f(f"{table}_cpf_cnpj_ukey"), f"{table}", ["cpf_cnpj"], unique=True)
    op.create_index(op.f(f"{table}_email_ukey"), f"{table}", ["email"], unique=True)
    op.create_index(op.f(f"{table}_subdomain_and_domain_ukey"), f"{table}", ["subdomain", "domain"], unique=True)
    op.execute(
        f"""
        CREATE TRIGGER update_{table}_modtime
            BEFORE UPDATE
            ON {table}
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_users_table() -> None:
    table = "users"
    op.create_table(
        table,
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(140), nullable=False),
        sa.Column("username", sa.String(70), nullable=False),
        sa.Column("email", sa.String(140), nullable=False),
        sa.Column("hashed_password", sa.String(144), nullable=False),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="False"),
        sa.Column("cell_phone", sa.String(15), nullable=True),
        sa.Column("thumbnail", sa.String(140), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="True"),
        *timestamps(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
    )
    op.create_index(op.f(f"{table}_username_ukey"), f"{table}", ["username"], unique=True),
    op.create_index(op.f(f"{table}_email_ukey"), f"{table}", ["email"], unique=True),
    op.execute(
        f"""
        CREATE TRIGGER update_{table}_modtime
            BEFORE UPDATE
            ON {table}
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_roles_table() -> None:
    table = "roles"
    op.create_table(
        table,
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(32), nullable=False),
        sa.Column("name", sa.String(70), nullable=False),
        *timestamps(),
    )
    op.create_index(op.f(f"{table}_slug_ukey"), f"{table}", ["slug"], unique=True),
    op.create_index(op.f(f"{table}_name_ukey"), f"{table}", ["name"], unique=True),
    op.execute(
        f"""
        CREATE TRIGGER update_{table}_modtime
            BEFORE UPDATE
            ON {table}
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_permissions_table() -> None:
    table = "permissions"
    op.create_table(
        table,
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(32), nullable=False),
        sa.Column("name", sa.String(70), nullable=False),
        *timestamps(),
    )
    op.create_index(op.f(f"{table}_slug_ukey"), f"{table}", ["slug"], unique=True),
    op.create_index(op.f(f"{table}_name_ukey"), f"{table}", ["name"], unique=True),
    op.execute(
        f"""
        CREATE TRIGGER update_{table}_modtime
            BEFORE UPDATE
            ON {table}
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_permissions_roles_table() -> None:
    table = "permissions_roles"
    op.create_table(
        table,
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("permission_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", UUID(as_uuid=True), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE", onupdate="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE", onupdate="CASCADE"),
    )
    op.create_index(
        op.f(f"{table}_permission_id_and_role_id_ukey"),
        f"{table}",
        ["permission_id", "role_id"],
        unique=True,
    ),
    op.execute(
        f"""
        CREATE TRIGGER update_{table}_modtime
            BEFORE UPDATE
            ON {table}
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_roles_users_table() -> None:
    table = "roles_users"
    op.create_table(
        table,
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("role_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE", onupdate="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", onupdate="CASCADE"),
    )
    op.create_index(
        op.f(f"{table}_role_id_and_user_id_ukey"),
        f"{table}",
        ["role_id", "user_id"],
        unique=True,
    ),
    op.execute(
        f"""
        CREATE TRIGGER update_{table}_modtime
            BEFORE UPDATE
            ON {table}
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_permissions_users_table() -> None:
    table = "permissions_users"
    op.create_table(
        table,
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("permission_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        *timestamps(),
    )
    sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE", onupdate="CASCADE"),
    sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", onupdate="CASCADE"),
    op.create_index(
        op.f(f"{table}_permission_id_and_user_id_ukey"),
        f"{table}",
        ["permission_id", "user_id"],
        unique=True,
    ),
    op.execute(
        f"""
        CREATE TRIGGER update_{table}_modtime
            BEFORE UPDATE
            ON {table}
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def insert_roles() -> None:
    op.execute(
        """
        INSERT INTO roles(slug, name) VALUES ('master', 'Gestão de domínio');
        INSERT INTO roles(slug, name) VALUES ('administration', 'Gestão');
        """
    )


def insert_permissions() -> None:
    op.execute(
        """
        INSERT INTO permissions(slug, name) VALUES ('tenants_manager', 'Gerenciar inquilinos');
        INSERT INTO permissions(slug, name) VALUES ('roles_manager', 'Gerenciar perfils');
        INSERT INTO permissions(slug, name) VALUES ('permissions_manager', 'Gerenciar permissões');
        INSERT INTO permissions(slug, name) VALUES ('users_manager', 'Gerenciar usuários');
        INSERT INTO permissions(slug, name) VALUES ('users_list', 'Listar usuários');
        INSERT INTO permissions(slug, name) VALUES ('users_show', 'Mostrar usuários');
        INSERT INTO permissions(slug, name) VALUES ('bank_accounts_manager', 'Gerenciar Contas Bancárias');
        INSERT INTO permissions(slug, name) VALUES ('bank_accounts_list', 'Listar Contas Bancárias');
        INSERT INTO permissions(slug, name) VALUES ('bank_accounts_show', 'Mostrar Contas Bancárias');
        """
    )


def insert_permissions_roles() -> None:
    op.execute(
        """ --# noqa: E501
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'tenants_manager\'), (SELECT id FROM roles WHERE slug=\'master\'));
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'roles_manager\'), (SELECT id FROM roles WHERE slug=\'master\'));
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'permissions_manager\'), (SELECT id FROM roles WHERE slug=\'master\'));
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'users_manager\'), (SELECT id FROM roles WHERE slug=\'master\'));
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'users_list\'), (SELECT id FROM roles WHERE slug=\'master\'));
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'users_show\'), (SELECT id FROM roles WHERE slug=\'master\'));
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'users_manager\'), (SELECT id FROM roles WHERE slug=\'administration\'));
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'users_list\'), (SELECT id FROM roles WHERE slug=\'administration\'));
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'users_show\'), (SELECT id FROM roles WHERE slug=\'administration\'));
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'bank_accounts_manager\'), (SELECT id FROM roles WHERE slug=\'administration\'));
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'bank_accounts_list\'), (SELECT id FROM roles WHERE slug=\'administration\'));
        INSERT INTO permissions_roles (permission_id, role_id) VALUES ((SELECT id FROM permissions WHERE slug=\'bank_accounts_show\'), (SELECT id FROM roles WHERE slug=\'administration\'));
        """
    )


def insert_domain_tenant() -> None:
    api_key = secrets.token_urlsafe(72)
    op.execute(
        f"""
        INSERT INTO tenants(name, brand, type, cpf_cnpj, cep, street, \
            number, complement, neighborhood, city, state, email, email_verified, phone, cell_phone, \
                api_key, subdomain, domain, is_master)
        VALUES ('Hyberica Ltda', 'Hyberica Softwares', 'Jurídica', '41.627.172/0001-77', '89500-214', \
            'Rua Adelmyr Pressanto', '211', 'Sala 1', 'Centro', 'Caçador', 'SC', '{EMAIL_MAIN}', true, null, null, \
                '{api_key}', '{HOST_MAIN}', '{DOMAIN_MAIN}', True);
        """
    )


def insert_user() -> None:
    master_hash_password = pwd_context.hash("master123")
    admin_hash_password = pwd_context.hash("admin123")
    op.execute(
        f"""
        INSERT INTO users(tenant_id, full_name, username, email, hashed_password, email_verified, is_active)
            VALUES ((SELECT id FROM tenants WHERE is_master), \
            'Master - Hyberica Ltda', 'master', '{EMAIL_MAIN}', '{master_hash_password}', true, true);
        INSERT INTO users(tenant_id, full_name, username, email, hashed_password, email_verified, is_active)
            VALUES ((SELECT id FROM tenants WHERE is_master), \
            'Administrador - Hyberica Ltda', 'admin', 'admin@hyberica.io', '{admin_hash_password}', true, true);
        """
    )
    op.execute(
        """
        INSERT INTO roles_users(role_id, user_id) VALUES ((SELECT id FROM roles WHERE slug='master'), \
            (SELECT id FROM users WHERE username='master'));
        INSERT INTO roles_users(role_id, user_id) VALUES ((SELECT id FROM roles WHERE slug='administration'), \
            (SELECT id FROM users WHERE username='admin'));
        """
    )


def upgrade():
    # create uuid extension for postgresql
    op.execute(
        """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """
    )

    # ### commands auto generated by Alembic - please adjust! ###
    create_updated_at_trigger()
    create_tenants_table()
    create_users_table()
    create_roles_table()
    insert_roles()
    create_permissions_table()
    insert_permissions()
    create_permissions_roles_table()
    insert_permissions_roles()
    create_roles_users_table()
    create_permissions_users_table()
    insert_domain_tenant()
    insert_user()
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("permissions_users")
    op.drop_table("roles_users")
    op.drop_table("permissions_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
    op.drop_table("tenants")
    op.execute("DROP TYPE person_types;")
    op.execute("DROP TYPE state_ufs;")
    op.execute("DROP FUNCTION update_updated_at_column")

    # drop uuid extension
    op.execute(
        """
        DROP EXTENSION IF EXISTS "uuid-ossp";
        """
    )
    # ### end Alembic commands ###
