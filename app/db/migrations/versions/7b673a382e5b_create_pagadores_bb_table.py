"""create_pagadores_bb_table

Revision ID: 7b673a382e5b
Revises: e9254a3fd852
Create Date: 2022-07-06 13:51:29.795654

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql.base import ENUM

from app.db.migrations.base import timestamps

# revision identifiers, used by Alembic.
revision = "7b673a382e5b"
down_revision = "e9254a3fd852"
branch_labels = None
depends_on = None
table = "pagadores_bb"


def create_pagadores_table() -> None:
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
        sa.Column("boleto_bb_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tipo_inscricao", ENUM(name="person_types", create_type=False), nullable=False),
        sa.Column("numero_inscricao", sa.String(19), nullable=False),
        sa.Column("nome", sa.String(30), nullable=False),
        sa.Column("endereco", sa.String(30), nullable=True),
        sa.Column("cep", sa.String(9), nullable=True),
        sa.Column("cidade", sa.String(30), nullable=True),
        sa.Column("bairro", sa.String(30), nullable=True),
        sa.Column("uf", ENUM(name="state_ufs", create_type=False), nullable=True),
        sa.Column("telefone", sa.String(30), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["boleto_bb_id"], ["boletos_bb.id"], ondelete="CASCADE", onupdate="CASCADE"),
        *timestamps(),
    )
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
    create_pagadores_table()


def downgrade():
    op.drop_table(table)
