from sqlalchemy import (
    String
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

import uuid

from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class Entity(Base):

    __tablename__ = "entities"

   
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),

        primary_key=True,

        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
        
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        
    )
    
    embedding: Mapped[list[float]] = mapped_column(
        Vector(1536),
        nullable=True
    )