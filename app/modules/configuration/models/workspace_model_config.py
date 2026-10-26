from uuid import UUID
from datetime import datetime

from sqlalchemy import (
    Integer,
    Numeric,
    String,
    DateTime,
    ForeignKey,
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


class WorkspaceModelConfig(Base):

    __tablename__ = "workspace_model_configs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    workspace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "workspaces.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    model_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "ai_models.id",
        ),
        nullable=False,
    )

    temperature: Mapped[float] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=0.2,
    )

    max_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2000,
    )

    mcp_tool: Mapped[str | None] = mapped_column(
        String(255),
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