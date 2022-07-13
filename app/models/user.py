from sqlalchemy import Boolean, Column, String
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    full_name = Column(String(140), nullable=False)
    username = Column(String(70), nullable=False)
    email = Column(String(140), nullable=False)
    hashed_password = Column(String(144), nullable=False)
    email_verified = Column(Boolean, nullable=False, server_default="False")
    cell_phone = Column(String(15), nullable=True)
    thumbnail = Column(String(140), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="True")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False)


metadata = sa.MetaData()

users = sa.Table(
    "users",
    metadata,
    sa.Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
        nullable=False,
        index=True,
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
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False, index=False),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False, index=False),
)
