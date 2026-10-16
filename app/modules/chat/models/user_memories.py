from uuid import UUID, uuid4
from datetime import datetime
from datetime import timezone
from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    Enum
)
from backend.app.modules.chat.enums.memories import MemoryType

from backend.app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column

class UserMemory(Base):
    __tablename__ = "user_memories"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
        
    )
    memory_type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType, native_enum=False, length=50),
        nullable=False, 
    )
    memory_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
        
    )
    importance: Mapped[int] = mapped_column(
        Integer,
        nullable= False,
        default = 5,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )