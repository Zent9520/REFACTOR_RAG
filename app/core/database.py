from sqlalchemy.ext.asyncio import (

    create_async_engine,

    async_sessionmaker,

    AsyncSession

)

from sqlalchemy.pool import NullPool

from sqlalchemy.orm import DeclarativeBase

import os

from app.core.settings import settings

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL chưa được cấu hình trong .env")


_pool_options = (
    {
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT_SECONDS,
        "pool_pre_ping": True,
    }
    if settings.DB_POOL_SIZE > 0 else {"poolclass": NullPool}
)

engine = create_async_engine(

    settings.DATABASE_URL,   # trước đây là DATABASE_URL
    echo=settings.DB_SQL_ECHO,


    connect_args={

        "statement_cache_size":

        0

    },


    **_pool_options

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
