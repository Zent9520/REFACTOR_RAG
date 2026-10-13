from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.core.database import Base


class Message(Base):

    __tablename__ = "messages"


    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )


    conversation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "conversations.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )


    role: Mapped[str] = mapped_column(
        String,
        nullable=False
    )


    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )