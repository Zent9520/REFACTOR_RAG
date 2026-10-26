from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DepartmentSensitivityPermission(Base):

    __tablename__ = "department_sensitivity_permissions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    owner_department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"),
        nullable=False,
    )

    viewer_department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"),
        nullable=False,
    )

    max_sensitivity_id: Mapped[int] = mapped_column(
        ForeignKey("sensitivity_levels.id"),
        nullable=False,
    )

    position_level_id: Mapped[int] = mapped_column(
        ForeignKey("position_levels.id"),
        nullable=False,
    )