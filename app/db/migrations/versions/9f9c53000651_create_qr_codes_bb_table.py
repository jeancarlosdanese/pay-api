"""create_qr_codes_bb_table

Revision ID: 90b50578e4e8
Revises: 7b673a382e5b
Create Date: 2022-07-07 14:12:55.442689

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID

from app.db.migrations.base import timestamps


# revision identifiers, used by Alembic.
revision = "90b50578e4e8"
down_revision = "7b673a382e5b"
branch_labels = None
depends_on = None
table = "qr_codes_bb"


def create_boletos_bb_qr_codes_table() -> None:
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
        sa.Column("url", sa.String(254), nullable=True),
        sa.Column("tx_id", sa.String(140), nullable=True),
        sa.Column("emv", sa.String(254), nullable=True),
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
    create_boletos_bb_qr_codes_table()


def downgrade():
    op.drop_table(table)
