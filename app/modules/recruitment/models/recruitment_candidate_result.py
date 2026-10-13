from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PG_UUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import Base


class RecruitmentCandidateResult(Base):

    __tablename__ = "recruitment_candidate_results"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recruitment_candidates.id"),
        nullable=False,
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    strengths: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    weaknesses: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    assessment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    raw_response: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )