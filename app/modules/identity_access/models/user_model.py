from uuid import UUID
from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Text,
)

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import Base


class User(Base):

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    
    access_token: Mapped[str] = mapped_column(
    Text,
    nullable=False,
)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )