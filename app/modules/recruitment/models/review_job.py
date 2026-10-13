from datetime import datetime
from datetime import timezone
from uuid import UUID
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.app.models.recruitment.review_task import ReviewTask
    
    


from app.core.database import Base


class ReviewJob(Base):

    __tablename__ = "review_jobs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    model_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ai_models.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    total_files: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    job_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc,
        ),
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    tasks: Mapped[list["ReviewTask"]] = relationship(
        "ReviewTask",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    
    
