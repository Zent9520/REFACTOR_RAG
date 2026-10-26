from sqlalchemy import (
    ForeignKey,
    Float,
    String
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
import uuid
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from pgvector.sqlalchemy import Vector


class EntityRelationship(Base):

    __tablename__ = "entity_relationships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),

        primary_key=True,

        default=uuid.uuid4
    )

    source_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id"),
        nullable=False
    )

    target_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id"),
        nullable=False
    )

    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0
    )
    
    chunk_id: Mapped[str] = (

    mapped_column(

        String(255),

        nullable=False
    )
)
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        
    )
    
    embedding: Mapped[list[float]] = mapped_column(
        Vector(1536),
        nullable=True
    )
    