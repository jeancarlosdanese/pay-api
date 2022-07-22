"""create_convenios_bancarios_table

Revision ID: 080f9dc5f5ac
Revises: 5c54e2c08763
Create Date: 2022-06-29 17:39:14.799397

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID

from app.db.migrations.base import timestamps

# revision identifiers, used by Alembic.
revision = "080f9dc5f5ac"
down_revision = "5c54e2c08763"
branch_labels = None
depends_on = None
table = "convenios_bancarios"


def create_convenios_bancarios_table() -> None:
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
        sa.Column("conta_bancaria_id", UUID(as_uuid=True), nullable=False),
        sa.Column("numero_convenio", sa.Integer, nullable=False),
        sa.Column("numero_carteira", sa.Integer, nullable=False),
        sa.Column("numero_variacao_carteira", sa.Integer, nullable=False),
        sa.Column("numero_dias_limite_recebimento", sa.Integer, nullable=False),
        sa.Column("descricao_tipo_titulo", sa.String(2), nullable=False),
        sa.Column("percentual_multa", sa.DECIMAL(), nullable=False, server_default="2.0"),
        sa.Column("percentual_juros", sa.DECIMAL(), nullable=False, server_default="1.0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="True"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["conta_bancaria_id"], ["contas_bancarias.id"], ondelete="RESTRICT", onupdate="RESTRICT"
        ),
        *timestamps(),
    )
    op.create_index(
        op.f(f"{table}_banco_id_and_numero_conta_index"),
        f"{table}",
        ["conta_bancaria_id", "numero_convenio"],
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
    create_convenios_bancarios_table()


def downgrade():
    op.drop_table(table)
