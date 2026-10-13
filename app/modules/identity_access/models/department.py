from sqlalchemy import (
    Integer,
    String
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.core.database import Base


class Department(Base):

    __tablename__ = (

        "departments"

    )


    id: Mapped[int] = (

        mapped_column(

            Integer,

            primary_key=True
        )   

    )


    name: Mapped[str | None] = (

        mapped_column(

            String(50),

            nullable=True
        )

    )