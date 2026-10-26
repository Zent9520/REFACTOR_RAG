from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class TagRoleRule(Base):
    __tablename__ = "tag_role_rules"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    tag_id:Mapped[int] = mapped_column (
        ForeignKey("tags.id")
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id")
    )