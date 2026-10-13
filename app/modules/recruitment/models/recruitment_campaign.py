from uuid import UUID
from datetime import datetime
from sqlalchemy import func, text

from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey
)

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from sqlalchemy.dialects.postgresql import JSONB

from pgvector.sqlalchemy import Vector

from app.core.database import Base


class RecruitmentCampaign(Base):

    __tablename__ = "recruitment_campaigns"

    id: Mapped[UUID] = mapped_column(
    PG_UUID(as_uuid=True),
    primary_key=True,
    server_default=text("gen_random_uuid()")
)

    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.id"),
        nullable=False
    )
    
    

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    job_description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft"
    )
    
    cv_embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
    )
    
    cv_data: Mapped[dict] = mapped_column(
    JSONB,
    nullable=False,
    default=lambda: {
        "candidates": []
    }
)

    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False
)

    updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False
)