from uuid import UUID
from datetime import datetime

from sqlalchemy import (
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


class MasterConfig(Base):

    __tablename__ = "master_configs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    embedding_model_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "embedding_models.id",
        ),
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