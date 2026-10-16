import asyncio

import backend.app.models_registry  # noqa: F401
from backend.app.core.database import Base, engine


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tạo bảng xong")


if __name__ == "__main__":
    asyncio.run(main())