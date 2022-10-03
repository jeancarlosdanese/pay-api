"""create_beneficiarios_bb_table

Revision ID: 9f9c53000651
Revises: 90b50578e4e8
Create Date: 2022-07-07 12:13:09.032188

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql.base import ENUM

from app.db.migrations.base import timestamps

# revision identifiers, used by Alembic.
revision = "9f9c53000651"
down_revision = "90b50578e4e8"
branch_labels = None
depends_on = None
table = "beneficiarios_bb"


def create_beneficiarios_table() -> None:
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
        sa.Column("agencia", sa.Integer, nullable=True),
        sa.Column("conta_corrente", sa.Integer, nullable=True),
        sa.Column("tipo_endereco", sa.Integer, nullable=True),
        sa.Column("logradouro", sa.String(30), nullable=True),
        sa.Column("bairro", sa.String(30), nullable=True),
        sa.Column("cidade", sa.String(30), nullable=True),
        sa.Column("codigo_cidade", sa.Integer, nullable=True),
        sa.Column("uf", ENUM(name="state_ufs", create_type=False), nullable=True),
        sa.Column("cep", sa.String(9), nullable=True),
        sa.Column("indicador_comprovacao", sa.String(1), nullable=True),
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
    create_beneficiarios_table()


def downgrade():
    op.drop_table(table)
