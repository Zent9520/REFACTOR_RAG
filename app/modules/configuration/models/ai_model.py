from uuid import UUID
from datetime import datetime


from sqlalchemy import (
    String,
    Boolean,
    DateTime
)

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.core.database import Base


class AIModel(Base):

    __tablename__ = "ai_models"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    model_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    display_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )