"""create_contas_bancarias_table

Revision ID: 5c54e2c08763
Revises: af8685d4bc29
Create Date: 2022-03-24 11:33:48.181230

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID

from app.db.migrations.base import timestamps
from app.schemas.enums import ContaBancariaType
from sqlalchemy.dialects.postgresql.base import ENUM


# revision identifiers, used by Alembic.
revision = "5c54e2c08763"
down_revision = "7139ccb5c56c"
branch_labels = None
depends_on = None
table = "contas_bancarias"


def create_contas_bancarias_table() -> None:
    conta_bancaria_types = tuple(ContaBancariaType.values())
    op.create_table(
        table,
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(140), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("banco_id", sa.Integer, nullable=False),
        sa.Column("tipo", ENUM(*conta_bancaria_types, name="conta_bancaria_types"), nullable=False),
        sa.Column("agencia", sa.Integer, nullable=True),
        sa.Column("agencia_dv", sa.Integer, nullable=False),
        sa.Column("numero_conta", sa.Integer, nullable=False),
        sa.Column("numero_conta_dv", sa.String(1), nullable=False),
        sa.Column("client_id", sa.String(170), nullable=True),
        sa.Column("client_secret", sa.String(254), nullable=True),
        sa.Column("developer_application_key", sa.String(70), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="True"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
        *timestamps(),
    )
    op.create_index(
        op.f(f"{table}_banco_id_and_numero_conta_index"), f"{table}", ["banco_id", "numero_conta"], unique=True
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


def upgrade():
    create_contas_bancarias_table()


def downgrade():
    op.drop_table(table)
    op.execute("DROP TYPE conta_bancaria_types;")
