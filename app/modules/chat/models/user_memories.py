from sqlalchemy import (
    String,
    Text,
    Integer,
    Enum
)
from backend.app.modules.chat.enums.memories import MemoryType

from backend.app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column

class UserMemory(Base):
    __tablename__ = "user_memories"
    user_email: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        index=True
        
    )
    memory_type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType),
        nullable=False, 
    )
    memory_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
        
    )
    importance: Mapped[int] = mapped_column(
        Integer,
        nullable= True,
        default = 5,
    )