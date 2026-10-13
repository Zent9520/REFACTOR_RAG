from uuid import UUID
from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Text,
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


class WorkspaceRagConfig(Base):

    __tablename__ = "workspace_rag_configs"

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

    master_config_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "master_configs.id",
        ),
        nullable=False,
    )

    data_source: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    chunking_strategy: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    top_k: Mapped[int] = mapped_column(
        Integer,
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
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
       
    )
    
    