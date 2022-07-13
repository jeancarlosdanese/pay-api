from sqlalchemy.dialects.postgresql.base import UUID

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.schema import Column


@as_declarative()
class Base:
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
