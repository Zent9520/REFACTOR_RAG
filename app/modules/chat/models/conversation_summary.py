from uuid import UUID
from uuid import uuid4
from datetime import datetime

from sqlalchemy import (
    Text,
    Integer,
    ForeignKey,
    DateTime
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from sqlalchemy.dialects.postgresql import (
    UUID as PG_UUID
)

from app.core.database import Base


class ConversationSummary(Base):

    __tablename__ = "conversation_summaries"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "conversations.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=""
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )

    last_processed_message_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )