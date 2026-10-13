from uuid import UUID
from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    DateTime,
    text,
)

from sqlalchemy.dialects.postgresql import (
    UUID as PG_UUID,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import Base


class Workspace(Base):

    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text(
            "gen_random_uuid()",
        ),
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    workspace_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )