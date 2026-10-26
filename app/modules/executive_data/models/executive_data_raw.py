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


class ExecutiveDataRaw(Base):

    __tablename__ = "executive_data_raw"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    dataset_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source_file: Mapped[str] = mapped_column(
        String(500),
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

    last_modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    file_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    report_data: Mapped[dict] = mapped_column(
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