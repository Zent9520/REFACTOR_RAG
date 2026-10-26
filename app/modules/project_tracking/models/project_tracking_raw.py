from uuid import UUID
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    Text,
    text,
)




from sqlalchemy.dialects.postgresql import (
    UUID as PG_UUID,
    JSONB,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import Base


class ProjectTrackingRaw(Base):

    __tablename__ = "project_tracking_raw"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    project_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    project_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    sharepoint_site_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sharepoint_drive_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sharepoint_item_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source_file: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    last_modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    project_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    project_data: Mapped[dict] = mapped_column(
        JSONB,
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