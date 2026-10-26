from sqlalchemy import *

from sqlalchemy.orm import *

from app.core.database import Base


class SensitivityLevel(

    Base

):


    __tablename__=(

        "sensitivity_levels"

    )


    id:Mapped[int] = (

        mapped_column(

            primary_key=True
        )

    )


    code:Mapped[str] = (

        mapped_column(

            String(50),

            unique=True
        )

    )


    is_sensitive:Mapped[bool]


    priority:Mapped[int | None] = (

        mapped_column(

            nullable=True
        )

    )


    description: Mapped[str | None] = (

        mapped_column(

            Text,

            nullable=True
        )

    )