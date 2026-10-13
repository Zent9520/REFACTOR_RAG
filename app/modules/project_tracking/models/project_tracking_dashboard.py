from uuid import UUID
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
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


class ProjectTrackingDashboard(Base):

    __tablename__ = "project_tracking_dashboard"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    project_code: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "project_tracking_raw.project_code",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    overall_health_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    overall_health_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    progress_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    progress_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    budget_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    budget_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    risk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    risk_total: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    task_analysis: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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