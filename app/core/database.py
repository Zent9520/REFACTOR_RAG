from sqlalchemy.ext.asyncio import (

    create_async_engine,

    async_sessionmaker,

    AsyncSession

)

from sqlalchemy.pool import NullPool

from sqlalchemy.orm import DeclarativeBase

import os

from backend.app.core.settings import settings

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL chưa được cấu hình trong .env")


engine = create_async_engine(

    settings.DATABASE_URL,   # trước đây là DATABASE_URL
    echo=True,


    connect_args={

        "statement_cache_size":

        0

    },


    poolclass=
    NullPool

)


AsyncSessionLocal = async_sessionmaker(

    bind=
    engine,


    expire_on_commit=
    False,


    class_=
    AsyncSession

)


class Base(
    DeclarativeBase
):
    pass



async def get_db():

    async with (
        AsyncSessionLocal()
    ) as session:

        yield session