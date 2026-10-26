from sqlalchemy import *

from sqlalchemy.orm import *

from app.core.database import Base


class PositionLevel(

    Base

):

    __tablename__ = (

        "position_levels"

    )


    id: Mapped[int] = (

        mapped_column(

            primary_key=True
        )

    )


    name: Mapped[str | None] = (

        mapped_column(

            String(50),

            nullable=True
        )

    )


    priority: Mapped[int | None] = (

        mapped_column(

            nullable=True
        )

    )