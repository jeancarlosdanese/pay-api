"""create_boletos_bb_table

Revision ID: e9254a3fd852
Revises: 080f9dc5f5ac
Create Date: 2022-07-06 12:06:53.921608

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID

from app.db.migrations.base import timestamps


# revision identifiers, used by Alembic.
revision = "e9254a3fd852"
down_revision = "080f9dc5f5ac"
branch_labels = None
depends_on = None
table = "boletos_bb"


def create_boletos_bb_table() -> None:

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
        sa.Column("convenio_bancario_id", UUID(as_uuid=True), nullable=False),
        sa.Column("numero_titulo_beneficiario", sa.Integer, nullable=False),
        sa.Column("data_emissao", sa.Date, nullable=False),
        sa.Column("data_vencimento", sa.Date, nullable=False),
        sa.Column("valor_original", sa.DECIMAL(), nullable=False),
        sa.Column("valor_desconto", sa.DECIMAL(), nullable=False, server_default="0.0"),
        sa.Column("descricao_tipo_titulo", sa.String(2), nullable=False),
        sa.Column("numero", sa.String(20), nullable=False),
        sa.Column("codigo_cliente", sa.Integer, nullable=True),
        sa.Column("linha_digitavel", sa.String(47), nullable=True),
        sa.Column("codigo_barra_numerico", sa.String(44), nullable=True),
        sa.Column("numero_contrato_cobranca", sa.Integer, nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["convenio_bancario_id"], ["convenios_bancarios.id"], ondelete="RESTRICT", onupdate="RESTRICT"
        ),
        *timestamps(),
    )
    op.create_index(
        op.f(f"{table}_convenio_bancario_id_and_numero_titulo_beneficiario_index"),
        f"{table}",
        ["convenio_bancario_id", "numero_titulo_beneficiario"],
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


def upgrade():
    create_boletos_bb_table()


def downgrade():
    op.drop_table(table)
