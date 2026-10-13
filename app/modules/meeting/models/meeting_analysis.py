# app/models/meeting_analysis.py

from uuid import UUID, uuid4
from datetime import datetime
from datetime import timezone

from sqlalchemy import (
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    JSON,
)

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import Base


class MeetingAnalysis(Base):

    __tablename__ = "meeting_analyses"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Microsoft Graph calendar event id
    event_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True,
    )

    # Teams OnlineMeeting ID - có thể chưa resolve được ngay
    online_meeting_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        index=True,
    )

    subject: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    body_preview: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    organizer_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    organizer_email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    web_link: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    join_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    online_meeting_provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    attendees: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Lưu raw metadata Graph để sau này cần field mới không phải sync lại
    raw_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    has_transcript: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    analysis_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    # AI RESULT
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    key_points: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    decisions: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    action_items: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    risks: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    unresolved_issues: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    model_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        onupdate=lambda: datetime.now(
            timezone.utc
        ),
    )
