from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


from app.core.database import Base


class SharePointDeltaState(Base):

    __tablename__ = "sharepoint_delta_states"

    site_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    drive_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    delta_link: Mapped[str] = mapped_column(Text, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)