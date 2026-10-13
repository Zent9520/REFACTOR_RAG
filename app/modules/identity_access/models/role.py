from sqlalchemy import *

from sqlalchemy.orm import *

from app.core.database import Base


class Role(Base):


    __tablename__ = (

        "roles"

    )


    id:Mapped[int] = (

        mapped_column(

            primary_key=True
        )

    )


    name: Mapped[str] = (

        mapped_column(

            String(50),

            unique=True
        )

    )


    description: Mapped[str | None] = (

        mapped_column(

            nullable=True
        )

    )


    department_id: Mapped[int | None] = (

        mapped_column(

            nullable=True
        )

    )


    position_level_id: Mapped[int | None] = (

        mapped_column(

            nullable=True
        )

    )