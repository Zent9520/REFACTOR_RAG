from sqlalchemy import (
    ForeignKey,
    String,
    Text
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
import uuid

from pgvector.sqlalchemy import Vector

from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID


class EntityContext(Base):

    __tablename__ = "entity_contexts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),

        primary_key=True,

        default=uuid.uuid4
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id"),
        nullable=False
    )

    chunk_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(1536),
        nullable=True
    )